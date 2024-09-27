#include <string>
#include <filesystem>
#include <chrono>

using namespace std;

#include "itkImage.h"
#include "itkImageFileReader.h"
#include "itkMemoryProbe.h"
#include "itkImageFileWriter.h"

#include "tools/ToolsItk.h"

int
main(int argc, char * argv[])
{

  // Verify command line arguments
  if (argc < 13)
  {
    std::cerr << "Usage: " << std::endl;
    std::cerr << argv[0] << " x y z vectorX vectorY vectorZ nbpoints outputFilename inputFile neighbors measurement typeBlock" <<std::endl;
    std::cout << "measurement: m for mean, d for median, n for min, x for max"  << std::endl;
    return EXIT_FAILURE;
  }

  int x = atoi(argv[1]);
  int y = atoi(argv[2]);
  int z = atoi(argv[3]);  
  double vectorX = atof(argv[4]);
  double vectorY = atof(argv[5]);
  double vectorZ = atof(argv[6]);
  int nbpoints = atoi(argv[7]);
  std::string outputFilename = argv[8];  
  std::string inputFile = argv[9];  
  int neighbors = atoi(argv[10]);
  char measurement = argv[11][0];
  int typeBlock = atoi(argv[12]);
  

  std::cout << "(" << x << ", " << y << ", " << z  << ")" << std::endl;
  std::cout << "vector ("  << vectorX << ", " << vectorY << ", " << vectorZ << ")"  << std::endl;
  std::cout << "nbpoints = " << nbpoints << std::endl;  
  std::cout << "output filename = " << outputFilename << std::endl;  
  std::cout << "input file = " << inputFile << std::endl;  
  std::cout << "neighbors  = " << neighbors  << std::endl;
  std::cout << "measurement = " << measurement << std::endl;
  std::cout << "typeBlock = " << typeBlock << std::endl;
  
  itk::MemoryProbe memoryProbe;

  std::cout << "We are measuring " << memoryProbe.GetType();
  std::cout << " in units of MB"  << ".\n" << std::endl;  
  memoryProbe.Start();
  auto start_timeP = std::chrono::high_resolution_clock::now(); 

  ToolsItk tool ;
  //int res = tool.computeProfile(x, y, z, vectorX, vectorY, vectorZ, nbpoints, filename, extension, inputDirectory, isDirectory, neighbors, measurement, typeBlock);
  int res = tool.computeProfile(x, y, z, vectorX, vectorY, vectorZ, nbpoints, outputFilename, inputFile, neighbors, measurement, typeBlock);
  std::cout << "res :" << res << std::endl;

  auto end_timeP = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> parallel_duration  = end_timeP - start_timeP;
    std::cout << "Parallel duration: "
              << parallel_duration.count() << " seconds"
              << std::endl; 

  memoryProbe.Stop();  
  std::cout << "** After allocation **" << std::endl;
  std::cout << "Mean: " << memoryProbe.GetMean()/1012 << std::endl;
  std::cout << "Total: " << memoryProbe.GetTotal()/1012 << std::endl;
  std::cout << "Max: " << memoryProbe.GetMaximum()/1012 << std::endl;
  std::cout << std::endl;
  
 return EXIT_SUCCESS;
}