#include <string>
#include <filesystem>
#include <Magick++.h>

using namespace std;
using namespace Magick;

//#include "itkImage.h"
//#include "itkImageFileReader.h"
#include "itkMemoryProbe.h"
//#include "itkImageFileWriter.h"


int
main(int argc, char * argv[])
{

  // Verify command line arguments
    if (argc < 5)
    {
        std::cerr << "Usage: " << std::endl;
        std::cerr << argv[0] << " inputDirectory begin end outputDirectory"  <<std::endl;
        return EXIT_FAILURE;
    }

    std::string inputDirectory = argv[1];
    int begin = atoi(argv[2]);
    int end = atoi(argv[3]);  
    std::string outputDirectory = argv[4];

    std::cout << "inputDirectory = " << inputDirectory << std::endl;
    std::cout << "begin = " << begin << std::endl;
    std::cout << "end = " << end << std::endl;  
    std::cout << "outputDirectory = " << outputDirectory << std::endl;
  

    clock_t cstart, cend;
    double time_taken;
    itk::MemoryProbe memoryProbe;
    std::vector<std::string> names ;

    for (const auto & entry : std::filesystem::directory_iterator(inputDirectory))
        {  
        names.push_back(entry.path());      
        }
  
    std::sort(names.begin(), names.end()); // sort  
    std::cout << "names size = " << names.size() << std::endl;
    std::cout << "names end = " << *(names.end()-1) << std::endl;
  
    std::string extension = (*(names.end()-1)).substr((*(names.end()-1)).find_last_of(".") + 1);
    std::cout << "extension = " << extension << std::endl;
    if(extension.compare("info") ==0) names.pop_back();
    std::cout << "names size = " << names.size() << std::endl;
    std::cout << "names end = " << *(names.end()-1) << std::endl;

    std::cout << "We are measuring " << memoryProbe.GetType();
    std::cout << " in units of MB"  << ".\n" << std::endl;
    cstart = clock();
    memoryProbe.Start();

    Image image;
    std::string outputFilename = "";
    int lastPos = 0;
    for(uint i= begin; i<end+1; i++ ) {    
        try{
            //std::cout << "inputFilename = " <<names.at(i) << std::endl;
            image.read(names.at(i));

            //image.resize(size + "x" + size);
            lastPos  = (names.at(i)).find_last_of("/") +1 ;
            outputFilename = (names.at(i)).substr(lastPos);
            //std::cout << "outputFilename 1 = " << outputFilename << std::endl;
            lastPos = outputFilename.find_last_of(".");
            outputFilename = outputFilename.substr(0,lastPos) + ".tiff" ;
            //std::cout << "outputFilename 2 = " << outputFilename << std::endl;
            //std::cout << "outputFilename 3 = " << outputDirectory  + outputFilename << std::endl;
            image.write(outputDirectory + outputFilename);
        }catch(Exception &error_ ){
            std:: cout << "Caught exception: " << error_.what() << std::endl;
            return -1;
        }
        }

  memoryProbe.Stop();
  cend = clock(); 
  std::cout << "** After allocation **" << std::endl;
  std::cout << "Mean: " << memoryProbe.GetMean()/1012 << std::endl;
  std::cout << "Total: " << memoryProbe.GetTotal()/1012 << std::endl;
  std::cout << "Max: " << memoryProbe.GetMaximum()/1012 << std::endl;
  std::cout << std::endl;
  time_taken = double(cend - cstart) / double(CLOCKS_PER_SEC);
  std::cout << "Time  : " << fixed
         << time_taken << setprecision(5);
  std::cout << " sec " << std::endl;

 return EXIT_SUCCESS;
}
