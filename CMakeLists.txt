cmake_minimum_required(VERSION 3.15)
project(limereport_pyqt6 LANGUAGES CXX)
if(NOT EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/vendor/LimeReport/CMakeLists.txt")
  message(FATAL_ERROR "vendor/LimeReport is missing: build from a checkout with submodules or from the sdist which vendors LimeReport 1.7.23")
endif()
# Apply our downstream fix to the pinned LimeReport submodule at configure time.
# A clean checkout and repeated CMake configuration are both supported.
find_package(Git REQUIRED)
set(LIMEREPORT_PATCH "${CMAKE_CURRENT_SOURCE_DIR}/patches/0001-repeat-group-header-on-footer-page.patch")
execute_process(
  COMMAND "${GIT_EXECUTABLE}" apply --reverse --check "${LIMEREPORT_PATCH}"
  WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/vendor/LimeReport"
  RESULT_VARIABLE LIMEREPORT_PATCH_ALREADY_APPLIED
  OUTPUT_QUIET ERROR_QUIET)
if(NOT LIMEREPORT_PATCH_ALREADY_APPLIED EQUAL 0)
  execute_process(
    COMMAND "${GIT_EXECUTABLE}" apply --check "${LIMEREPORT_PATCH}"
    WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/vendor/LimeReport"
    RESULT_VARIABLE LIMEREPORT_PATCH_CAN_APPLY
    OUTPUT_VARIABLE LIMEREPORT_PATCH_OUTPUT
    ERROR_VARIABLE LIMEREPORT_PATCH_ERROR)
  if(NOT LIMEREPORT_PATCH_CAN_APPLY EQUAL 0)
    message(FATAL_ERROR "LimeReport patch cannot be applied. Check pinned submodule revision and local modifications: ${LIMEREPORT_PATCH_ERROR}")
  endif()
  execute_process(
    COMMAND "${GIT_EXECUTABLE}" apply "${LIMEREPORT_PATCH}"
    WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/vendor/LimeReport"
    RESULT_VARIABLE LIMEREPORT_PATCH_RESULT)
  if(NOT LIMEREPORT_PATCH_RESULT EQUAL 0)
    message(FATAL_ERROR "Failed to apply LimeReport downstream patch")
  endif()
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
install(
    TARGETS _core
    LIBRARY DESTINATION limereport_pyqt6 COMPONENT python
    RUNTIME DESTINATION limereport_pyqt6 COMPONENT python
)
