#include <string>
#include <filesystem>
#include <vector>
#include <chrono>
using namespace std;

#include "itkImage.h"
#include "itkImageFileReader.h"
#include "itkMemoryProbe.h"
#include "itkTileImageFilter.h"
#include "itkImageFileWriter.h"

#include "tools/ToolsItk.h"

int
main(int argc, char * argv[])
{
  
    // Verify command line arguments
  if (argc < 12)
  {
    std::cerr << "Usage: " << std::endl;
    std::cerr << argv[0] << " inputdirectory" << " sizex sizey sizez px py pz posInArea outputFile factorResize extension"<< " / positionInArea = c for center or o for origin" <<std::endl;
    return EXIT_FAILURE;
  }

  std::string inputDirectory = argv[1];
  uint sizeX = stoi(argv[2]);
  uint sizeY = stoi(argv[3]);
  uint sizeZ = stoi(argv[4]);
  uint px = stoi(argv[5]);
  uint py = stoi(argv[6]);
  uint pz = stoi(argv[7]);
  std::string positionInArea = argv[8];
  std::string outputFilename = argv[9];
  uint factorResize = stoi(argv[10]);
  std::string extension = argv[11];
  
  itk::MemoryProbe memoryProbe;
  
  std::cout << "We are measuring " << memoryProbe.GetType();
  //std::cout << " in units of " << memoryProbe.GetUnit() << ".\n" << std::endl;
  std::cout << " in units of MB"  << ".\n" << std::endl;
  
  memoryProbe.Start();
  auto start_timeP = std::chrono::high_resolution_clock::now(); 

  ToolsItk tool ;
  int res = tool.createRoi(inputDirectory, sizeX, sizeY, sizeZ, px, py, pz, positionInArea, outputFilename, factorResize, extension);
  std::cout << "res :" << res << std::endl;
  auto end_timeP = std::chrono::high_resolution_clock::now();
  std::chrono::duration<double> parallel_duration  = end_timeP - start_timeP;
  std::cout << "duration: "
              << parallel_duration.count() << " seconds"
              << std::endl; 

  memoryProbe.Stop();  
  std::cout << "** After allocation **" << std::endl;
  std::cout << "Mean: " << memoryProbe.GetMean()/1000 << std::endl;
  std::cout << "Total: " << memoryProbe.GetTotal()/1000 << std::endl;
  std::cout << "Max: " << memoryProbe.GetMaximum()/1000 << std::endl;
  std::cout << std::endl;
  
  return EXIT_SUCCESS;
}
  