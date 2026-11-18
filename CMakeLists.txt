cmake_minimum_required(VERSION 3.15)
project(limereport_pyqt6 LANGUAGES CXX)
if(NOT EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/vendor/LimeReport/CMakeLists.txt")
  message(FATAL_ERROR "vendor/LimeReport is missing: build from a checkout with submodules or from the sdist which vendors LimeReport 1.7.23")
endif()
# Apply the pinned downstream change without relying on Git metadata.
# Source distributions contain vendor files but no valid submodule .git directory.
find_package(Python COMPONENTS Interpreter REQUIRED)
execute_process(
  COMMAND "${Python_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/scripts/apply_lime_patch.py"
          "${CMAKE_CURRENT_SOURCE_DIR}/vendor/LimeReport/limereport/lrreportrender.cpp"
  RESULT_VARIABLE LIMEREPORT_PATCH_RESULT
  OUTPUT_VARIABLE LIMEREPORT_PATCH_OUTPUT
  ERROR_VARIABLE LIMEREPORT_PATCH_ERROR)
if(NOT LIMEREPORT_PATCH_RESULT EQUAL 0)
  message(FATAL_ERROR "Cannot apply LimeReport downstream fix: ${LIMEREPORT_PATCH_ERROR}")
endif()
find_package(pybind11 CONFIG REQUIRED)
find_package(Qt6 QUIET COMPONENTS Core)
set(USE_QT6 ON CACHE BOOL "" FORCE)
set(LIMEREPORT_STATIC ON CACHE BOOL "" FORCE)
set(LIMEREPORT_DEMO OFF CACHE BOOL "" FORCE)
set(ENABLE_DIALOG_DESIGNER OFF CACHE BOOL "" FORCE)
set(HAVE_UI_LOADER OFF CACHE BOOL "" FORCE)
set(ENABLE_ZINT OFF CACHE BOOL "" FORCE)
set(CMAKE_INSTALL_DEFAULT_COMPONENT_NAME LimeReportDevelopment)
add_subdirectory(vendor/LimeReport)
set(CMAKE_INSTALL_DEFAULT_COMPONENT_NAME Unspecified)
pybind11_add_module(_core MODULE cpp/bindings.cpp)
target_compile_features(_core PRIVATE cxx_std_17)
target_link_libraries(_core PRIVATE limereport-qt6)
if(DEFINED Python_EXECUTABLE)
  execute_process(
    COMMAND "${Python_EXECUTABLE}" -c "from PyQt6.QtCore import QT_VERSION_STR; print(QT_VERSION_STR)"
    OUTPUT_VARIABLE LIMEREPORT_PYQT6_QT_VERSION
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET)
endif()
if(LIMEREPORT_PYQT6_QT_VERSION AND DEFINED Qt6_VERSION)
  string(REGEX MATCH "^[0-9]+\\.[0-9]+" LIMEREPORT_PYQT6_QT_MM "${LIMEREPORT_PYQT6_QT_VERSION}")
  string(REGEX MATCH "^[0-9]+\\.[0-9]+" LIMEREPORT_QT_MM "${Qt6_VERSION}")
  if(NOT LIMEREPORT_PYQT6_QT_MM STREQUAL LIMEREPORT_QT_MM)
    message(WARNING "Qt ${Qt6_VERSION} builds _core but PyQt6 bundles Qt ${LIMEREPORT_PYQT6_QT_VERSION}: use a matching Qt SDK")
  endif()
endif()
if(APPLE)
  set_target_properties(_core PROPERTIES INSTALL_RPATH "@loader_path;@loader_path/../PyQt6/Qt6/lib" BUILD_WITH_INSTALL_RPATH TRUE INSTALL_RPATH_USE_LINK_PATH FALSE)
elseif(UNIX)
  set_target_properties(_core PROPERTIES INSTALL_RPATH "$ORIGIN:$ORIGIN/../PyQt6/Qt6/lib" BUILD_WITH_INSTALL_RPATH TRUE INSTALL_RPATH_USE_LINK_PATH FALSE)
endif()
# Record the Qt version used to compile the extension in the wheel.
configure_file("${CMAKE_CURRENT_SOURCE_DIR}/cpp/_build_qt.py.in"
               "${CMAKE_CURRENT_BINARY_DIR}/_build_qt.py" @ONLY)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/_build_qt.py"
        DESTINATION limereport_pyqt6 COMPONENT python)
install(
    TARGETS _core
    LIBRARY DESTINATION limereport_pyqt6 COMPONENT python
    RUNTIME DESTINATION limereport_pyqt6 COMPONENT python
)
