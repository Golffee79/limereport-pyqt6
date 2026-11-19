#include <pybind11/pybind11.h>

#include <QApplication>
#include <QCoreApplication>
#include <QObject>
#include <QStandardItemModel>
#include <QVariant>

#include <cmath>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

#include "lrreportengine.h"
#include "../vendor/LimeReport/limereport/lrscriptenginemanager.h"

namespace py = pybind11;

QVariant to_variant(const py::handle& value)
{
    if (value.is_none()) {
        return QVariant();
    }
    if (py::isinstance<py::bool_>(value)) {
        return QVariant::fromValue(value.cast<bool>());
    }
    if (py::isinstance<py::int_>(value)) {
        try {
            return QVariant::fromValue(value.cast<qint64>());
        } catch (const py::cast_error&) {
            throw py::value_error("integer must fit in a signed 64-bit value");
        }
    }
    if (py::isinstance<py::float_>(value)) {
        double number = value.cast<double>();
        if (!std::isfinite(number)) {
            throw py::value_error("float must be finite");
        }
        return QVariant::fromValue(number);
    }
    if (py::isinstance<py::str>(value)) {
        return QString::fromStdString(value.cast<std::string>());
    }
    throw py::type_error("value must be None, bool, int, float, or str");
}

QString name_from_python(const py::handle& value, const char* description)
{
    if (!py::isinstance<py::str>(value)) {
        throw py::type_error(std::string(description) + " must be str");
    }
    QString name = QString::fromStdString(value.cast<std::string>());
    if (name.isEmpty()) {
        throw py::value_error(std::string(description) + " must not be empty");
    }
    return name;
}

std::vector<QString> column_names(const py::handle& values)
{
    if (!py::isinstance<py::list>(values) && !py::isinstance<py::tuple>(values)) {
        throw py::type_error("columns must be a list or tuple of str");
    }

    py::sequence sequence = values.cast<py::sequence>();
    if (sequence.empty()) {
        throw py::value_error("columns must not be empty");
    }

    std::vector<QString> columns;
    columns.reserve(sequence.size());
    for (const py::handle& item : sequence) {
        QString column = name_from_python(item, "column name");
        for (const QString& existing : columns) {
            if (existing == column) {
                throw py::value_error("column names must be unique");
            }
        }
        columns.push_back(column);
    }
    return columns;
}

class ReportEngine
{
    inline static int live_engines = 0;
public:
    ReportEngine()
    {
        if (QApplication::instance() == nullptr) {
            throw std::runtime_error("Create a PyQt6 QApplication before ReportEngine");
        }
        engine = std::make_unique<LimeReport::ReportEngine>();
        ++live_engines;
    }

    ~ReportEngine()
    {
        if (QCoreApplication::closingDown()) {
            // ponytail: process exit reclaims this after Qt has started teardown.
            engine.release();
        } else {
            engine.reset();
            if (--live_engines == 0) {
                LimeReport::ScriptEngineManager::destroyIfExists();
            }
        }
    }

    bool load_from_file(const py::handle& path)
    {
        return engine->loadFromFile(path_from_python(path));
    }

    bool save_to_file(const py::handle& path)
    {
        QString file_path = path_from_python(path);
        ensure_loaded();
        return engine->saveToFile(file_path);
    }

    std::string last_error() const
    {
        return engine->lastError().toStdString();
    }

    void design()
    {
        engine->designReport();
    }

    void preview()
    {
        engine->previewReport();
    }

    bool export_pdf(const py::handle& path, const py::handle& progress)
    {
        QString file_path = path_from_python(path);
        ensure_loaded();
        if (progress.is_none()) {
            return engine->printToPDF(file_path);
        }
        if (!py::isinstance<py::function>(progress)) {
            throw py::type_error("progress must be callable or None");
        }
        py::function callback = progress.cast<py::function>();
        QMetaObject::Connection connection = QObject::connect(
            engine.get(), &LimeReport::ReportEngine::renderPageFinished,
            [&callback](int page) {
                py::gil_scoped_acquire gil;
                try {
                    callback(page);
                } catch (const py::error_already_set&) {
                    PyErr_WriteUnraisable(PyUnicode_FromString("limereport progress callback"));
                }
            });
        bool result = engine->printToPDF(file_path);
        QObject::disconnect(connection);
        return result;
    }

    void set_variable(const py::handle& name, const py::handle& value)
    {
        engine->dataManager()->setReportVariable(name_from_python(name, "variable name"),
                                                 to_variant(value));
    }

    void set_data(const py::handle& name, const py::handle& rows, const py::handle& columns)
    {
        QString data_name = name_from_python(name, "data source name");
        if (!py::isinstance<py::list>(rows)) {
            throw py::type_error("rows must be a list");
        }
        if (!columns.is_none() && !py::isinstance<py::list>(columns)
            && !py::isinstance<py::tuple>(columns)) {
            throw py::type_error("columns must be a list or tuple of str");
        }

        py::list row_list = rows.cast<py::list>();
        std::vector<QString> headers;
        std::vector<std::vector<QVariant>> values;

        if (row_list.empty()) {
            if (columns.is_none()) {
                throw py::value_error("empty rows require columns");
            }
            headers = column_names(columns);
        } else if (py::isinstance<py::dict>(row_list[0])) {
            if (!columns.is_none()) {
                throw py::value_error("columns must be omitted for dict rows");
            }
            py::dict first = row_list[0].cast<py::dict>();
            for (const auto& item : first) {
                headers.push_back(name_from_python(item.first, "column name"));
            }
            if (headers.empty()) {
                throw py::value_error("dict rows must not be empty");
            }
            for (const QString& header : headers) {
                int duplicates = 0;
                for (const QString& candidate : headers) {
                    if (candidate == header) {
                        ++duplicates;
                    }
                }
                if (duplicates > 1) {
                    throw py::value_error("column names must be unique");
                }
            }
            for (const py::handle& row : row_list) {
                if (!py::isinstance<py::dict>(row)) {
                    throw py::type_error("rows must all be dict or all be list/tuple");
                }
                py::dict mapping = row.cast<py::dict>();
                if (mapping.size() != headers.size()) {
                    throw py::value_error("dict rows must have identical keys");
                }
                std::vector<QVariant> current;
                current.reserve(headers.size());
                for (const QString& header : headers) {
                    py::str key(header.toStdString());
                    if (!mapping.contains(key)) {
                        throw py::value_error("dict rows must have identical keys");
                    }
                    current.push_back(to_variant(mapping[key]));
                }
                values.push_back(std::move(current));
            }
        } else {
            if (columns.is_none()) {
                throw py::value_error("list or tuple rows require columns");
            }
            headers = column_names(columns);
            for (const py::handle& row : row_list) {
                if (!py::isinstance<py::list>(row) && !py::isinstance<py::tuple>(row)) {
                    throw py::type_error("rows must all be dict or all be list/tuple");
                }
                py::sequence sequence = row.cast<py::sequence>();
                if (sequence.size() != headers.size()) {
                    throw py::value_error("row length must match columns");
                }
                std::vector<QVariant> current;
                current.reserve(headers.size());
                for (const py::handle& value : sequence) {
                    current.push_back(to_variant(value));
                }
                values.push_back(std::move(current));
            }
        }

        auto model = std::make_unique<QStandardItemModel>();
        QStringList labels;
        for (const QString& header : headers) {
            labels.append(header);
        }
        model->setHorizontalHeaderLabels(labels);
        for (const std::vector<QVariant>& row : values) {
            QList<QStandardItem*> items;
            for (const QVariant& value : row) {
                auto* item = new QStandardItem();
                item->setData(value, Qt::DisplayRole);
                items.append(item);
            }
            model->appendRow(items);
        }

        if (!engine->dataManager()->addModel(data_name, model.get(), true)) {
            throw std::runtime_error(engine->lastError().toStdString());
        }
        model.release();
    }

private:
    QString path_from_python(const py::handle& value) const
    {
        if (!py::isinstance<py::str>(value)) {
            throw py::type_error("path must be str");
        }
        QString path = QString::fromStdString(value.cast<std::string>());
        if (path.isEmpty()) {
            throw py::value_error("path must not be empty");
        }
        return path;
    }

    void ensure_loaded() const
    {
        if (engine->reportFileName().isEmpty()) {
            throw std::runtime_error("Load a report before saving or exporting");
        }
    }

    std::unique_ptr<LimeReport::ReportEngine> engine;
};

PYBIND11_MODULE(_core, module)
{
    module.doc() = "Native bindings for LimeReport PyQt6";
    py::class_<ReportEngine>(module, "ReportEngine")
        .def(py::init<>())
        .def("load_from_file", &ReportEngine::load_from_file)
        .def("save_to_file", &ReportEngine::save_to_file)
        .def("last_error", &ReportEngine::last_error)
        .def("set_variable", &ReportEngine::set_variable)
        .def("set_data", &ReportEngine::set_data, py::arg("name"), py::arg("rows"),
             py::arg("columns") = py::none())
        .def("design", &ReportEngine::design)
        .def("preview", &ReportEngine::preview)
        .def("export_pdf", &ReportEngine::export_pdf, py::arg("path"),
             py::arg("progress") = py::none());
}
