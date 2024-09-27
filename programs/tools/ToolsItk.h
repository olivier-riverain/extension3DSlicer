#ifndef TOOLSITK_H
#define TOOLSITK_H

#include <string>

#include "itkImage.h"
#include "itkImageFileReader.h"

using PixelType = unsigned int;
using ImageType2D = itk::Image<PixelType, 2>;
using ImageType3D = itk::Image<PixelType, 3>;
using ImageReaderType = itk::ImageFileReader<ImageType2D>;
using ImageReaderType3D = itk::ImageFileReader<ImageType3D>;
using IndexType = itk::Index<2>; 
using IndexType3D = itk::Index<3>; 


// Define class ToolsItk
class ToolsItk{

public:
    int resizeImage(std::string inputDirectory, int begin, int end,  int factorResize, std::string output, std::string extension);
    int stack2Dto3D(std::string inputDirectory, int beginX, int endX, int beginY, int endY, int beginZ, int endZ, std::string output, bool resize, int factorResize, std::string extension);    
    int changeSizeImage(ImageType2D::Pointer imageOrigin, ImageType2D::Pointer imageNew, int factorResize, int beginX, int endX, int beginY, int endY);
    int createRoi(std::string inputDirectory, int sizeX, int sizeY, int sizeZ, int px, int py, int pz, std::string positionInArea, std::string outputFile, uint factorResize, std::string extension);
    int resizeImageParall(std::string inputDirectory, int begin, int end,  int factorResize, std::string output, std::string extension);
    int stack2Dto3DParall(std::string inputDirectory, int beginX, int endX, int beginY, int endY, int beginZ, int endZ, std::string output, bool resize, int factorResize, std::string extension); 
    int cleanList(std::vector<std::string> names, std::vector<std::string> &namesClean, std::string extension);
    int resizeImageParallV2(std::string inputDirectory, int begin, int end,  int factorResize, std::string output, std::string extension);
    int stack2Dto3DParallV2(std::string inputDirectory, int beginX, int endX, int beginY, int endY, int beginZ, int endZ, std::string output, bool resize, int factorResize, std::string extension); 
    int computeProfile(int x, int y, int z, double vectorX, double vectorY, double vectorZ, int nbpoints, std::string outputFilename, std::string inputFile, int distanceNeighbors, char measurement, int typeBlock);
    int displayProfile(std::string filename);    
    int computeMeasurement(int px, int py, int pz, double baseVector1[], double baseVector2[], int distance, ImageType3D::Pointer image, char measurement, int dimension);
    int listOfValuesFromNeighbors(int px, int py, int pz, int distance, ImageType3D::Pointer image, std::vector<uint> &tab);    
    int listOfValuesFromNeighbors2D(int px, int py, int pz, double baseVector1[], double baseVector2[], int distance, ImageType3D::Pointer image, std::vector<uint> &tab);
    int computeDistanceMean(std::vector<uint> tab);
    int computeDistanceMedian(std::vector<uint> tab);
    int computeDistanceMin(std::vector<uint> tab);
    int computeDistanceMax(std::vector<uint> tab);
    int computeBaseVector(double * vector, double * baseVector1,  double * baseVector2);

protected:

private:

};
#endif

