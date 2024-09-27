cmake_minimum_required (VERSION 3.5)
project(itkdgtal)

set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)



# rechercher opencv
find_package( OpenCV REQUIRED )
include_directories( ${OpenCV_INCLUDE_DIRS} )

# Rechercher la bibliothèque Qt5
find_package(Qt5 COMPONENTS Widgets Gui REQUIRED)

# Rechercher la bibliothèque Qt6
#find_package(Qt6 COMPONENTS Widgets Gui REQUIRED)

# Rechercher la bibliothèque ImageMagick
find_package(ImageMagick COMPONENTS Magick++ REQUIRED)
include_directories(${ImageMagick_INCLUDE_DIRS})


# Rechercher la bibliothèque itk
#list(APPEND CMAKE_PREFIX_PATH "/net/cremi/jchaveroux/espaces/travail/Travail/M2/PFE/ITK/ITK-build") # attention à modifier pour chaque ordinateur
#list(APPEND CMAKE_PREFIX_PATH "/net/cremi/oriverain/espaces/travail/m2/pfe/logiciels/itk-build") # attention à modifier pour chaque ordinateur

find_package(ITK REQUIRED)
include(${ITK_USE_FILE})
message("ITK_USE_FILE : ${ITK_USE_FILE}")
message("CMAKE_PREFIX_PATH : ${CMAKE_PREFIX_PATH}")

# Rechercher la bibliothèque dgtal
#list(APPEND CMAKE_PREFIX_PATH "/net/cremi/oriverain/espaces/travail/m2/pfe/logiciels/DGtal-1.3/build") # attention à modifier pour chaque ordinateur
find_package(DGtal REQUIRED)
INCLUDE_DIRECTORIES(${DGTAL_INCLUDE_DIRS})
LINK_DIRECTORIES(${DGTAL_LIBRARY_DIRS})
message("DGTAL_LIBRARIES: ${DGTAL_LIBRARIES}")
message("DGTAL_INCLUDE_DIRS: ${DGTAL_INCLUDE_DIRS}")
message("DGTAL found")

# Rechercher la bibliothèque vtk
#list(APPEND CMAKE_PREFIX_PATH "/net/cremi/jchaveroux/espaces/travail/Travail/M2/PFE/VTK/VTK-build") # attention à modifier pour chaque ordinateur
#list(APPEND CMAKE_PREFIX_PATH "/net/cremi/oriverain/espaces/travail/m2/pfe/logiciels/VTK-9.3.0/build") # attention à modifier pour chaque ordinateur
find_package(VTK REQUIRED)
message("VTK FOUND")

find_package(Boost REQUIRED)
message("Boost_LIBRARIES: ${Boost_LIBRARIES}")
message("Boost FOUND")

# rechercher la bibliotheque OpenMP
find_package(OpenMP REQUIRED)
if(OpenMP_CXX_FOUND)
 message("OpenMP FOUND")
endif()

# rechercher la bibliotheque QGLVIEWER
FIND_PACKAGE(QGLVIEWER REQUIRED)
INCLUDE_DIRECTORIES(${QGLVIEWER_INCLUDE_DIR}) 
message("QGLViewer FOUND")

file(GLOB SOURCES tools/*.cpp)
file(GLOB HEADERS tools/*.h)

#add_executable(getImageSize ${SOURCES} ${HEADERS})
add_executable(getImageSize getImageSize.cpp )
add_executable(cropImageRegion cropImageSpecRegion.cpp )
add_executable(minMax minMax.cpp )
add_executable(measureMem measureMem.cpp )
add_executable(stack2to3d stack2Dto3D.cpp)
add_executable(createRoiImage3D createRoiImage3D.cpp ${SOURCES} ${HEADERS})
add_executable(zoom zoom.cpp)
add_executable(zoom3D zoom3D.cpp)
add_executable(streamapipeline streamapipeline.cpp)
add_executable(stack2to3dstream stack2Dto3DStreaming.cpp)
add_executable(essai essai.cpp)
add_executable(divideInBlocks divideInBlocks.cpp)
#add_executable(createMip createMip.cpp ${SOURCES} ${HEADERS})
add_executable(resizeImage resizeImage.cpp ${SOURCES} ${HEADERS})
add_executable(convertTo convertTo.cpp)
add_executable(parallelize parallelize.cpp ${SOURCES} ${HEADERS})
add_executable(resizeImageParall resizeImageParall.cpp ${SOURCES} ${HEADERS})
add_executable(test_resizeImageParall test_resizeImageParall.cpp ${SOURCES} ${HEADERS})
add_executable(test_createRoiImage3D test_createRoiImage3D.cpp ${SOURCES} ${HEADERS})
add_executable(resizeImageParallV2 resizeImageParallV2.cpp ${SOURCES} ${HEADERS})
add_executable(test_resizeImageParallV2 test_resizeImageParallV2.cpp ${SOURCES} ${HEADERS})
add_executable(computeProfile computeProfile.cpp ${SOURCES} ${HEADERS})
add_executable(displayProfile displayProfile.cpp ${SOURCES} ${HEADERS})


target_link_libraries(getImageSize ${ITK_LIBRARIES})
target_link_libraries(cropImageRegion ${ITK_LIBRARIES})
target_link_libraries(minMax ${ITK_LIBRARIES} ${VTK_LIBRARIES})
target_link_libraries(measureMem ${ITK_LIBRARIES})
target_link_libraries(stack2to3d ${ITK_LIBRARIES})
target_link_libraries(createRoiImage3D ${ITK_LIBRARIES} OpenMP::OpenMP_CXX)
target_link_libraries(zoom ${ITK_LIBRARIES})
target_link_libraries(zoom3D ${ITK_LIBRARIES})
target_link_libraries(streamapipeline ${ITK_LIBRARIES})
target_link_libraries(stack2to3dstream ${ITK_LIBRARIES})
target_link_libraries(essai ${ITK_LIBRARIES})
target_link_libraries(divideInBlocks ${ITK_LIBRARIES})
#target_link_libraries(createMip ${ITK_LIBRARIES} OpenMP::OpenMP_CXX)
target_link_libraries(resizeImage ${ITK_LIBRARIES} OpenMP::OpenMP_CXX)
target_link_libraries(convertTo  ${ITK_LIBRARIES} ${ImageMagick_LIBRARIES})
target_link_libraries(parallelize  ${ITK_LIBRARIES} OpenMP::OpenMP_CXX)
target_link_libraries(resizeImageParall ${ITK_LIBRARIES} OpenMP::OpenMP_CXX)
target_link_libraries(test_resizeImageParall ${ITK_LIBRARIES} OpenMP::OpenMP_CXX)
target_link_libraries(test_createRoiImage3D ${ITK_LIBRARIES} OpenMP::OpenMP_CXX)
target_link_libraries(resizeImageParallV2 ${ITK_LIBRARIES} OpenMP::OpenMP_CXX)
target_link_libraries(test_resizeImageParallV2 ${ITK_LIBRARIES} OpenMP::OpenMP_CXX)
target_link_libraries(computeProfile ${ITK_LIBRARIES} OpenMP::OpenMP_CXX)
target_link_libraries(displayProfile ${ITK_LIBRARIES} OpenMP::OpenMP_CXX)

#target_link_libraries(vol2normalField  ${ITK_LIBRARIES}  ${VTK_LIBRARIES} ${Boost_LIBRARIES} ${DGTAL_LIBRARIES})
#target_link_libraries(nrrdtovol  ${ITK_LIBRARIES}  ${VTK_LIBRARIES} ${Boost_LIBRARIES} ${DGTAL_LIBRARIES})
#target_link_libraries(displayvol  Qt5::Widgets Qt5::Gui ${ITK_LIBRARIES}  ${Boost_LIBRARIES} ${DGTAL_LIBRARIES} ${QGLVIEWER_LIBRARIES} )
#target_link_libraries(voltonormals  ${ITK_LIBRARIES}   ${Boost_LIBRARIES} ${DGTAL_LIBRARIES})
#target_link_libraries(3dVolMarchingCube  ${ITK_LIBRARIES}   ${Boost_LIBRARIES} ${DGTAL_LIBRARIES})

vtk_module_autoinit(
  #TARGETS itk2vol
  #TARGETS itk2vol vol2normalField
  #TARGETS nrrdtovol
  TARGETS minMax
  MODULES ${VTK_LIBRARIES}
)


