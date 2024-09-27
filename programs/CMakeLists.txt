cmake_minimum_required (VERSION 3.5)
project(citrusSkin)

# search library ImageMagick
find_package(ImageMagick COMPONENTS Magick++ REQUIRED)
include_directories(${ImageMagick_INCLUDE_DIRS})

# search library itk
find_package(ITK REQUIRED)
include(${ITK_USE_FILE})
message("ITK_USE_FILE : ${ITK_USE_FILE}")
message("CMAKE_PREFIX_PATH : ${CMAKE_PREFIX_PATH}")

# search library OpenMP
find_package(OpenMP REQUIRED)
if(OpenMP_CXX_FOUND)
 message("OpenMP FOUND")
endif()


file(GLOB SOURCES tools/*.cpp)
file(GLOB HEADERS tools/*.h)

#add_executable(getImageSize ${SOURCES} ${HEADERS})
add_executable(createRoiImage3D createRoiImage3D.cpp ${SOURCES} ${HEADERS})
add_executable(resizeImage resizeImage.cpp ${SOURCES} ${HEADERS})
add_executable(convertTo convertTo.cpp)
add_executable(resizeImageParall resizeImageParall.cpp ${SOURCES} ${HEADERS})
add_executable(resizeImageParallV2 resizeImageParallV2.cpp ${SOURCES} ${HEADERS})
add_executable(computeProfile computeProfile.cpp ${SOURCES} ${HEADERS})
add_executable(displayProfile displayProfile.cpp ${SOURCES} ${HEADERS})

target_link_libraries(createRoiImage3D ${ITK_LIBRARIES} OpenMP::OpenMP_CXX)
target_link_libraries(resizeImage ${ITK_LIBRARIES} OpenMP::OpenMP_CXX)
target_link_libraries(convertTo  ${ITK_LIBRARIES} ${ImageMagick_LIBRARIES})
target_link_libraries(resizeImageParall ${ITK_LIBRARIES} OpenMP::OpenMP_CXX)
target_link_libraries(resizeImageParallV2 ${ITK_LIBRARIES} OpenMP::OpenMP_CXX)
target_link_libraries(computeProfile ${ITK_LIBRARIES} OpenMP::OpenMP_CXX)
target_link_libraries(displayProfile ${ITK_LIBRARIES} OpenMP::OpenMP_CXX)





