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
  if (argc < 7)
  {
    std::cerr << "Usage: " << std::endl;
    std::cerr << argv[0] << " inputDirectory begin end factorResize outputImage extension" << "  example factorResize = 8 to divide the size by 8" <<std::endl;
    return EXIT_FAILURE;
  }

  std::string inputDirectory = argv[1];
  int begin = atoi(argv[2]);
  int end = atoi(argv[3]);  
  int factorResize = atoi(argv[4]);
  std::string outputImage = argv[5];
  std::string extension = argv[6];

  std::cout << "inputDirectory = " << inputDirectory << std::endl;
  std::cout << "begin = " << begin << std::endl;
  std::cout << "end = " << end << std::endl;
  std::cout << "factorResize = " << factorResize << std::endl;
  std::cout << "outputImage = " << outputImage << std::endl;
  
  itk::MemoryProbe memoryProbe;

  std::cout << "We are measuring " << memoryProbe.GetType();
  std::cout << " in units of MB"  << ".\n" << std::endl;  
  memoryProbe.Start();
  auto start_timeP = std::chrono::high_resolution_clock::now(); 

  ToolsItk tool ;
  int res = tool.resizeImageParall(inputDirectory, begin, end, factorResize, outputImage, extension);
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