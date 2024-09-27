/**
 * \file ToolsItk.cpp
 * @brief Tools to manipulate images
 * 
 * \author Olivier Riverain
 * \version 1.0
 * \date september 2024
 * @copyright   GNU Public License
 *
 * List of functions to manipulate images
 *
 */

#include <iostream>
#include <string>
#include <filesystem>
#include <omp.h>
#include <chrono>
#include <cstdlib>
#include <cmath>


#include "ToolsItk.h"

#include "itkImage.h"
#include "itkTileImageFilter.h"
#include "itkImageFileReader.h"
#include "itkImageFileWriter.h"
#include "itkMinimumMaximumImageCalculator.h"
#include "itkImageRegionIterator.h"
#include "itkOffset.h"


using namespace std;


/** 
 * @brief Resize and stack several 2D images in a 3D image (sequential version)
 * 
 * @param inputDirectory the directory that contains all the slices
 * @param begin the first slice
 * @param end the last slice
 * @param factorResize the image reduction factor
 * @param output the name of the output file
 * @param extension the extension of the slices
 * @return the return value of the function stack2Dto3D 
*/
int ToolsItk::resizeImage(std::string inputDirectory, int begin, int end, int factorResize, std::string output, std::string extension) {
    
    int res =0;
    if(factorResize == 1) {
        res = stack2Dto3D(inputDirectory, -1, 0, -1, 0, begin, end, output, false, factorResize, extension);
    } else {
        res = stack2Dto3D(inputDirectory, -1, 0, -1, 0, begin, end, output, true, factorResize, extension);
    }    
    std::cout << "res = " << res << std::endl;
    return res;
}


/** 
 * @brief Resize and stack several 2D images in a 3D image (parallelized version)
 * 
 * @param inputDirectory the directory that contains all the slices
 * @param begin the first slice
 * @param end the last slice
 * @param factorResize the image reduction factor
 * @param output the name of the output file
 * @param extension the extension of the slices
 * @return the return value of the function stack2Dto3DParall 
*/
int ToolsItk::resizeImageParall(std::string inputDirectory, int begin, int end, int factorResize, std::string output, std::string extension) {
    
    int res =0;
    if(factorResize == 1) {
        res = stack2Dto3DParall(inputDirectory, -1, 0, -1, 0, begin, end, output, false, factorResize, extension);
    } else {
        res = stack2Dto3DParall(inputDirectory, -1, 0, -1, 0, begin, end, output, true, factorResize, extension);
    }    
    std::cout << "res = " << res << std::endl;
    return res;
}

/** 
 * @brief stack several 2D images in a 3D image (sequencial version)
 * 
 * @param inputDirectory the directory that contains all the slices
 * @param beginX the first position of the pixel in the x axis
 * @param endX the last position of the pixel in the x axis
 * @param beginY the first position of the pixel in the y axis
 * @param endY the last position of the pixel in the y axis
 * @param beginZ the first position of the pixel in the z axis
 * @param endZ the last position of the pixel in the z axis 
 * @param output the name of the ouput file
 * @param resize true if the image must be reduced
 * @param factorResize the image reduction factor 
 * @param extension the format of the slices to be processed, example: jp2
 * @return returns 0 if no problem encountered during image manipulation 
*/
int ToolsItk::stack2Dto3D(std::string inputDirectory,  int beginX, int endX, int beginY, int endY, int beginZ, int endZ, std::string output, bool resize, int factorResize, std::string extension) {
    
    std::vector<std::string> names;
    std::vector<std::string> namesClean;
    using PixelType = unsigned int;  
    constexpr unsigned int InputImageDimension = 2;
    constexpr unsigned int OutputImageDimension = 3;
    

    using InputImageType = itk::Image<PixelType, InputImageDimension>;
    using OutputImageType = itk::Image<PixelType, OutputImageDimension>;

    using ImageReaderType = itk::ImageFileReader<InputImageType>;

    using TilerType = itk::TileImageFilter<InputImageType, OutputImageType>;
  
    for (const auto & entry : std::filesystem::directory_iterator(inputDirectory))
        {  
        names.push_back(entry.path());      
        }
  
    std::sort(names.begin(), names.end()); // sort
  //std::vector<std::string>::iterator nit;  
  /*for (nit = names.begin(); nit != names.end(); ++nit)
  {
    std::cout << "File: " << (*nit).c_str() << std::endl;    
  }*/
    /*std::cout << "names size = " << names.size() << std::endl;
    std::cout << "names end = " << *(names.end()-1) << std::endl;
  
    std::string extension = (*(names.end()-1)).substr((*(names.end()-1)).find_last_of(".") + 1);
    std::cout << "extension = " << extension << std::endl;
    if(extension.compare("info") ==0) names.pop_back();
    std::cout << "names size = " << names.size() << std::endl;
    std::cout << "names end = " << *(names.end()-1) << std::endl;*/

    cleanList(names, namesClean, extension);
    std::cout << "namesClean size = " << namesClean.size() << std::endl;
    if(namesClean.size() < (endZ-beginZ+1)) {
        std::cerr << "There are not enough files with extension " << extension << std::endl;
        return -1;
    }

    
    std::cout << "inputDirectory = " << inputDirectory << std::endl;
    std::cout << "factorResize = " << factorResize << std::endl;
    std::cout << "outputImage = " << output << std::endl;
    std::cout << "begin = " << beginZ << std::endl;
    std::cout << "end = " << endZ << std::endl;

    if(endZ > namesClean.size()-1) {
        std::cout << "The point can't be in the area, axis Z." << std::endl;
        return -1;
    } 

    /*for (int i=beginZ; i<endZ+1; i++)
    {
        std::cout << "File: " << namesClean.at(i) << std::endl;    
    }**/
 
    auto tiler = TilerType::New();

    itk::FixedArray<unsigned int, OutputImageDimension> layout;

    layout[0] = 1;
    layout[1] = 1;
    layout[2] = 0;

    tiler->SetLayout(layout);

    unsigned int inputImageNumber = 0;

    auto reader = ImageReaderType::New();

    InputImageType::Pointer inputImageTile;    
    //int cpt =0; 
    
    /*if(resize) {          
        for (int i=beginZ; i<endZ+1; i= i +factorResize) // we keep 1 slide every factorResize slide
        {             
            std::cout << " " << i << std::endl;
            reader->SetFileName(namesClean.at(i));
            std::cout << "stack2Dto3D avant reader->UpdateLargestPossibleRegion()" << std::endl;            
            reader->UpdateLargestPossibleRegion();            
            inputImageTile = reader->GetOutput();
            //std::cout << "stack2Dto3D apres reader->GetOutput()" << std::endl;  
            InputImageType::Pointer imageNew;
            imageNew = ImageType2D::New();
            //std::cout << "stack2Dto3D avant  changeSizeImage" << std::endl;            
            int res = changeSizeImage(inputImageTile, imageNew, factorResize, beginX, endX, beginY, endY);
            //std::cout << "stack2Dto3D après changeSizeImage" << std::endl;            
            ImageType2D::RegionType regionNew = imageNew->GetLargestPossibleRegion();            
            ImageType2D::SizeType sizeNew = regionNew.GetSize();            
            inputImageTile->DisconnectPipeline();
            tiler->SetInput(inputImageNumber++, imageNew);            
            cpt++;
        }
    
    } else {             
        for (int i=beginZ; i<endZ+1; i++)
        {            
            reader->SetFileName(namesClean.at(i));
            reader->UpdateLargestPossibleRegion();
            inputImageTile = reader->GetOutput();          
            inputImageTile->DisconnectPipeline();
            tiler->SetInput(inputImageNumber++, inputImageTile);
            cpt++;
        }        
    } */

     for (int i=beginZ; i<endZ+1; i= i + factorResize) // we keep 1 slide every factorResize slide
        {             
            std::cout << " " << i << std::endl;
            reader->SetFileName(namesClean.at(i));
            //std::cout << "stack2Dto3D avant reader->UpdateLargestPossibleRegion()" << std::endl;            
            reader->UpdateLargestPossibleRegion();            
            inputImageTile = reader->GetOutput();
            //std::cout << "stack2Dto3D apres reader->GetOutput()" << std::endl;
            if(resize) { 
                InputImageType::Pointer imageNew;
                imageNew = ImageType2D::New();
                //std::cout << "stack2Dto3D avant  changeSizeImage" << std::endl;            
                int res = changeSizeImage(inputImageTile, imageNew, factorResize, beginX, endX, beginY, endY);
                //std::cout << "stack2Dto3D après changeSizeImage" << std::endl;            
                //ImageType2D::RegionType regionNew = imageNew->GetLargestPossibleRegion();            
                //ImageType2D::SizeType sizeNew = regionNew.GetSize();            
                inputImageTile->DisconnectPipeline();
                tiler->SetInput(inputImageNumber++, imageNew); 
            } else {
                inputImageTile->DisconnectPipeline();
                tiler->SetInput(inputImageNumber++, inputImageTile);                
            }                       
            //cpt++;
        }      
         
    std::cout << "inputImageNumber = " << inputImageNumber << std::endl; 

    PixelType filler = 128;

    tiler->SetDefaultPixelValue(filler);

    tiler->Update();
    
    try
    {
        itk::WriteImage(tiler->GetOutput(), output);
    }
    catch (const itk::ExceptionObject & excp)
    {
        std::cerr << excp << std::endl;
        return EXIT_FAILURE;
    }

    return 0;  
}

/** 
 * @brief stack several 2D images in a 3D image (parallelized version 1)
 * 
 * @param inputDirectory the directory that contains all the slices
 * @param beginX the first position of the pixel in the x axis
 * @param endX the last position of the pixel in the x axis
 * @param beginY the first position of the pixel in the y axis
 * @param endY the last position of the pixel in the y axis
 * @param beginZ the first position of the pixel in the z axis
 * @param endZ the last position of the pixel in the z axis 
 * @param output the name of the ouput file
 * @param resize true if the image must be reduced
 * @param factorResize the image reduction factor 
 * @param extension the format of the slices to be processed, example: jp2
 * @return returns 0 if no problem encountered during image manipulation 
*/
int ToolsItk::stack2Dto3DParall(std::string inputDirectory,  int beginX, int endX, int beginY, int endY, int beginZ, int endZ, std::string output, bool resize, int factorResize, std::string extension) {
    std::cout << "omp_get_num_procs () = " << omp_get_num_procs() << std::endl;
    omp_set_num_threads(omp_get_num_procs()); // pour définir le nombre de threads voir si on rajoute un paramètre dans la fonction
    //std::cout << "number of threads = " << omp_get_num_threads() << std::endl;    
    std::vector<std::string> names ;
    std::vector<std::string> namesClean;
    using PixelType = unsigned int;  
    constexpr unsigned int InputImageDimension = 2;
    constexpr unsigned int OutputImageDimension = 3;    

    using InputImageType = itk::Image<PixelType, InputImageDimension>;
    using OutputImageType = itk::Image<PixelType, OutputImageDimension>;

    using ImageReaderType = itk::ImageFileReader<InputImageType>;

    using TilerType = itk::TileImageFilter<InputImageType, OutputImageType>;
  
    for (const auto & entry : std::filesystem::directory_iterator(inputDirectory))
        {  
        names.push_back(entry.path());      
        }
  
    std::sort(names.begin(), names.end()); // sort
  //std::vector<std::string>::iterator nit;  
  /*for (nit = names.begin(); nit != names.end(); ++nit)
  {
    std::cout << "File: " << (*nit).c_str() << std::endl;    
  }*/
    //std::cout << "names size = " << names.size() << std::endl;
    //std::cout << "names end = " << *(names.end()-1) << std::endl;  
    
    cleanList(names, namesClean, extension);
    //std::cout << "namesClean size = " << namesClean.size() << std::endl;
    if(namesClean.size() < (endZ-beginZ+1)) {
        std::cerr << "There are not enough files with extension " << extension << std::endl;
        return -1;
    }
    
    std::cout << "inputDirectory = " << inputDirectory << std::endl;
    std::cout << "factorResize = " << factorResize << std::endl;
    std::cout << "outputImage = " << output << std::endl;
    std::cout << "begin = " << beginZ << std::endl;
    std::cout << "end = " << endZ << std::endl;

    if(endZ > namesClean.size()-1) {
        std::cout << "The point can't be in the area, axis Z." << std::endl;
        return -1;
    } 

    /*for (int i=beginZ; i<endZ+1; i++)
    {
        std::cout << "File: " << namesClean.at(i) << std::endl;    
    }*/
 
    auto tiler = TilerType::New();

    itk::FixedArray<unsigned int, OutputImageDimension> layout;

    layout[0] = 1;
    layout[1] = 1;
    layout[2] = 0;

    tiler->SetLayout(layout);

    unsigned int inputImageNumber = 0;

    auto reader = ImageReaderType::New();

    InputImageType::Pointer inputImageTile;
    InputImageType::RegionType region;
    int cpt =0;

    std::vector<ImageType2D::Pointer> tabImages((endZ-beginZ+1)/factorResize+1);
    std::vector<int> tabIndex((endZ-beginZ+1)/factorResize+1);
    std::cout << "tabImages size = " << tabImages.size() << std::endl;
    std::cout << "tabIndex size = " << tabIndex.size() << std::endl;
    for(uint i=0; i<tabImages.size(); i++ ) {
        tabImages[i] = NULL;
    }
    for(uint i=0; i<tabIndex.size(); i++ ) {
        tabIndex[i] = 0;
    }
    int th_id, nthreads;
    int stack =-1;
    std::chrono::duration<double> duration_load;
    double totalTimeLoad = 0;
    std::chrono::duration<double> duration_changeSizeImage;
    double totalTimeChangeSizeImage = 0;
    std::chrono::duration<double> duration_stack;
    double totalStack = 0;
    std::chrono::duration<double> duration_write;
    double totalWrite = 0;
    //#pragma omp parallel for ordered shared(stack) private(th_id)
    #pragma omp parallel for  shared(stack) private(th_id) schedule(dynamic, 4)
    for (int i=beginZ; i<endZ+1; i= i +factorResize)
    {            
        th_id = omp_get_thread_num();
        //printf("Hello World 0 from thread %d i = %d imod = %d stack = %d\n", th_id, i, (i-beginZ)/factorResize, stack);
        auto start_timeLoad = std::chrono::high_resolution_clock::now();          
        ImageType2D::Pointer image = itk::ReadImage<ImageType2D>(namesClean.at(i));
        auto end_timeLoad = std::chrono::high_resolution_clock::now();
        duration_load = end_timeLoad - start_timeLoad;
        totalTimeLoad += duration_load.count();
        if (resize) {
            ImageType2D::Pointer imageNew;
            imageNew = ImageType2D::New();
            auto start_changeSizeImage = std::chrono::high_resolution_clock::now();             
            int res = changeSizeImage(image, imageNew, factorResize, beginX, endX, beginY, endY);
            auto end_changeSizeImage = std::chrono::high_resolution_clock::now();
            duration_changeSizeImage = end_changeSizeImage - start_changeSizeImage;
            totalTimeChangeSizeImage +=  duration_changeSizeImage.count();                       
            tabImages[(i-beginZ)/factorResize] = imageNew;            
        } else {
            tabImages[i-beginZ] = image;                
        }
            
        tabIndex[(i-beginZ)/factorResize] = 1;
            printf("Hello World from thread %d i = %d imod = %d stack = %d\n", th_id, i, (i-beginZ)/factorResize, stack);
            std::cout << "tabIndex : ";
            for(uint i=0; i<tabIndex.size(); i++ ) {
                std::cout << tabIndex[i] << " ";
            }
            std::cout << std::endl;       
        
        #pragma omp critical
        {
        auto start_stack = std::chrono::high_resolution_clock::now();
        while(tabIndex[stack+1] == 1) {
            //std::cout << namesClean.at((stack+1)*factorResize+beginZ) << std::endl;                        
            tiler->SetInput(inputImageNumber++, tabImages[stack+1]);   
            tabImages[stack+1] = NULL;
            tabIndex[stack+1] = -1;
            stack++;                              
        }
        auto end_stack = std::chrono::high_resolution_clock::now();
        duration_stack = end_stack - start_stack;
        totalStack +=  duration_stack.count(); 
        }

        cpt++;
    }
    std::cout << "Time load mean = " << totalTimeLoad/((endZ-beginZ+1)/factorResize) << std::endl;
    std::cout << "Time changeSizeImage mean = " << totalTimeChangeSizeImage/((endZ-beginZ+1)/factorResize) << std::endl;
    std::cout << "Time stack mean = " << totalStack/((endZ-beginZ+1)/factorResize) << std::endl;
    std::cout << "tabIndex final: ";
    for(uint i=0; i<tabIndex.size(); i++ ) {
        std::cout << tabIndex[i] << " ";
    }
    std::cout << std::endl;    
     
    std::cout << "inputImageNumber = " << inputImageNumber << std::endl; 
    auto start_write = std::chrono::high_resolution_clock::now();
    PixelType filler = 128;

    tiler->SetDefaultPixelValue(filler);
    std::cout << "stack2Dto3DParall ici 1 " << std::endl; 
    tiler->Update();
     
    try
    {
        itk::WriteImage(tiler->GetOutput(), output);
    }
    catch (const itk::ExceptionObject & excp)
    {
        std::cerr << excp << std::endl;
        return EXIT_FAILURE;
    }
    auto end_write = std::chrono::high_resolution_clock::now();
    duration_write = end_write - start_write;
    totalWrite +=  duration_write.count();
    std::cout << "Time write = " << totalWrite << std::endl; 
    return 0;  
}

/** 
 * @brief clean list of files by extension
 * 
 * @param names the list of names of the slices
 * @param namesClean the list of names of the slices after cleaning
 * @param extensionPattern the pattern of the extension 
 * @return returns 0 if no problem encountered during image manipulation 
*/
int ToolsItk::cleanList(std::vector<std::string> names, std::vector<std::string> &namesClean, std::string extensionPattern) {
    std::string extension = "";
    std::cout << "cleanList names size = " << names.size() << std::endl;
    for(uint i =0; i< names.size(); i++) {
        extension = (names.at(i)).substr((names.at(i)).find_last_of(".") + 1);
        if(extension.compare(extensionPattern) == 0) namesClean.push_back(names.at(i));         
    }
    std::cout << "cleanList namesClean size = " << namesClean.size() << std::endl;
    return 0;
}

/** 
 * @brief resize a 2D image
 * 
 * @param imageOrigin the pointer to the original image
 * @param imageNew the pointer to the new resized image
 * @param factorResize the image reduction factor 
 * @param beginX the first position of the pixel in the x axis
 * @param endX the last position of the pixel in the x axis
 * @param beginY the first position of the pixel in the y axis
 * @param endY the last position of the pixel in the y axis
 * @return returns 0 if no problem encountered during image manipulation 
*/
int ToolsItk::changeSizeImage(ImageType2D::Pointer imageOrigin, ImageType2D::Pointer imageNew, int factorResize, int beginX, int endX, int beginY, int endY) {
    using IndexType = itk::Index<2>; 
    IndexType indexOrigin;
    ImageType2D::RegionType regionOrigin = imageOrigin->GetLargestPossibleRegion();
    ImageType2D::SizeType sizeOrigin = regionOrigin.GetSize();
    //std::cout << "x sizeOrigin[0] = " << sizeOrigin[0] << std::endl;
    //std::cout << "y sizeOrigin[1] = " << sizeOrigin[1] << std::endl;
    if(endX > sizeOrigin[0]-1) {
        std::cout << "The point can't be in the area, axis x,  " << endX << " > " << sizeOrigin[0]-1 << std::endl;
        return -1;
    }
    if(endY > sizeOrigin[1]-1) {
        std::cout << "The point can't be in the area, axis y, "  << endY << " > " << sizeOrigin[1]-1 << std::endl;
        return -1;
    }
    ImageType2D::IndexType corner = { { 0, 0 } };
    ImageType2D::SizeType sizeNew;
    unsigned int NumRows;
    unsigned int NumCols;
    int maxX = 0;
    int maxY =0;
    int minX =0;
    int minY =0;
    if(beginX == -1 || beginY == -1) {        
        NumCols = sizeOrigin[0]/factorResize+1;
        NumRows = sizeOrigin[1]/factorResize+1;        
        //std::cout << "NumCols = " << NumCols << std::endl;
        //std::cout << "NumRows = " << NumRows << std::endl;
        maxX = sizeOrigin[0];
        maxY = sizeOrigin[1];      
    } else {
        NumCols = endX - beginX + 1;
        NumRows = endY - beginY + 1;
        minX = beginX;
        minY = beginY;
        maxX = endX+1;
        maxY = endY+1;
    }
           
    sizeNew[0] = NumCols;
    sizeNew[1] = NumRows;
    //std::cout << "x sizeNew[0] = " << sizeNew[0] << std::endl;
    //std::cout << "y sizeNew[1] = " << sizeNew[1] << std::endl;
    //std::cout << "minY = " << minY << std::endl;
    //std::cout << "maxY = " << maxY << std::endl;
    //std::cout << "minX = " << minX << std::endl;
    //std::cout << "maxX = " << maxX << std::endl;
    ImageType2D::RegionType region(corner, sizeNew);
    imageNew->SetRegions(region);
    imageNew->Allocate();
    ImageType2D::IndexType indexNew;
    for(uint y=0; y<NumRows; y++) {
        for(uint x=0; x<NumCols; x++) {
            indexNew[1] = y;
            indexNew[0] = x;  
            imageNew->SetPixel(indexNew, 0);
        }
    }    
    // mettre un iterator
    uint cpty =0;
    uint cptx =0;    
    for(int y=minY; y<maxY; y= y+factorResize) { 
      indexOrigin[1]= y;
      cptx=0;          
      for(int x=minX; x<maxX; x= x+factorResize) { 
        indexOrigin[0]= x;        
        indexNew[1] = cpty;
        indexNew[0] = cptx;
        //std::cout << "(" << indexOrigin[1]  <<  ", " << indexOrigin[0] << ") -> (" << indexNew[1]  <<  ", " << indexNew[0] << ")"  << std::endl;        
        imageNew->SetPixel(indexNew, imageOrigin->GetPixel(indexOrigin));            
        cptx++;              
      }
      cpty++;
    }
    /*std::cout << "changeSizeImage debut iterator " << std::endl;
    constexpr unsigned int Dimension2D = 2;    
    using PixelType = unsigned int;
    using ImageType2D = itk::Image<PixelType, Dimension2D>;    
    using ConstIteratorType = itk::ImageRegionConstIterator<ImageType2D>;
    using IteratorType = itk::ImageRegionIterator<ImageType2D>;
    ImageType2D::RegionType inputRegion;
    ImageType2D::RegionType::IndexType inputStart;
    ImageType2D::RegionType::SizeType inputSize;
    inputStart[0] = minX;
    inputStart[1] = minY;
    inputSize[0] = maxX;
    inputSize[1] = maxY;
    inputRegion.SetSize(inputSize);
    inputRegion.SetIndex(inputStart);
    ImageType2D::RegionType outputRegion;
    ImageType2D::RegionType::IndexType outputStart;
    ImageType2D::RegionType::SizeType outputSize;
    outputStart[0] = 0;
    outputStart[1] = 0;    
    outputSize[0] = maxX / factorResize;
    outputSize[1] = maxY / factorResize;
    //std::cout << "changeSizeImage iterator 2 " << std::endl;
    outputRegion.SetSize(outputSize);
    outputRegion.SetIndex(outputStart);
    ConstIteratorType inputIt(imageOrigin, inputRegion);
    IteratorType outputIt(imageNew, outputRegion);
    inputIt.GoToBegin();
    outputIt.GoToBegin();    
    //std::cout << "changeSizeImage iterator 3 " << std::endl;
    while (!inputIt.IsAtEnd())
    {
        outputIt.Set(inputIt.Get());        
        for (unsigned int i = 0; i < factorResize; ++i) {
            if (!inputIt.IsAtEnd()) {
                ++inputIt;
            }
        }
        ++outputIt;
    }    
    std::cout << "changeSizeImage fin iterator " << std::endl;*/
    return 0;
}

/** 
 * @brief create a region of interest (ROI)
 * 
 * @param inputDirectory the directory that contains all the slices
 * @param sizeX the dimension of the area in the x axis
 * @param sizeY the dimension of the area in the y axis
 * @param sizeZ the dimension of the area in the z axis
 * @param px the original position of the area in the x axis
 * @param py the original position of the area in the y axis
 * @param pz the original position of the area in the z axis
 * @param positionInArea the nature of the original position, example c for center
 * @param outputFile the name of the ouput file 
 * @param factorResize the image reduction factor 
 * @param extension the format of the slices to be processed, example: jp2
 * @return returns 0 if no problem encountered during image manipulation 
*/
int ToolsItk::createRoi(std::string inputDirectory, int sizeX, int sizeY, int sizeZ, int px, int py, int pz, std::string positionInArea, std::string outputFile, uint factorResize, std::string extension) {
    int difX = px;
    int difY = py;
    int difZ = pz;
    uint somX = px;
    uint somY = py;
    uint somZ = pz;
    if(positionInArea.compare("c")==0) {
        std::cout << "c => center" << std::endl;
        difX = px-sizeX/2;
        difY = py-sizeY/2;
        difZ = pz-sizeZ/2;
        somX = px+sizeX/2;
        somY = py+sizeY/2;
        somZ = pz+sizeZ/2;
    }
    std::cout << "difx = " << difX << std::endl;
    std::cout << "dify = " << difY << std::endl;
    std::cout << "difz = " << difZ << std::endl;
    std::cout << "somx = " << somX << std::endl;
    std::cout << "somy = " << somY << std::endl;
    std::cout << "somz = " << somZ << std::endl;
    if((difX <0) || (difY < 0) | (difZ <0)) {
        std::cout << "The point can't be in the area." << std::endl;
        return -1;
    }

    int res =0;
    int beginX = difX;
    int beginY = difY;
    int beginZ = difZ;
    int endX = difX + sizeX - 1;
    int endY = difY + sizeY - 1;
    int endZ = difZ + sizeZ - 1;
    //res = stack2Dto3D(inputDirectory, beginX, endX, beginY, endY, beginZ, endZ, outputFile, true, factorResize);  
    res = stack2Dto3DParall(inputDirectory, beginX, endX, beginY, endY, beginZ, endZ, outputFile, true, factorResize, extension);    
    //std::cout << "res = " << res << std::endl;
    return res;   
}



/** 
 * @brief resize and stack several 2D images in a 3D image (parallel version)
 * 
 * @param inputDirectory the directory that contains all the slices
 * @param begin the first slice
 * @param end the last slice
 * @param factorResize the image reduction factor
 * @param output the name of the output file
 * @param extension the extension of the slices
 * @return the return value of the function stack2Dto3DParallV2 
*/
int ToolsItk::resizeImageParallV2(std::string inputDirectory, int begin, int end, int factorResize, std::string output, std::string extension) {    
    int res =0;
    if(factorResize == 1) {
        res = stack2Dto3DParallV2(inputDirectory, -1, 0, -1, 0, begin, end, output, false, factorResize, extension);
    } else {
        res = stack2Dto3DParallV2(inputDirectory, -1, 0, -1, 0, begin, end, output, true, factorResize, extension);
    }    
    std::cout << "res = " << res << std::endl;
    return res;
}


/** 
 * @brief stack several 2D images in a 3D image (parallel version 2)
 * 
 * @param inputDirectory the directory that contains all the slices
 * @param beginX the first position of the pixel in the x axis
 * @param endX the last position of the pixel in the x axis
 * @param beginY the first position of the pixel in the y axis
 * @param endY the last position of the pixel in the y axis
 * @param beginZ the first position of the pixel in the z axis
 * @param endZ the last position of the pixel in the z axis 
 * @param output the name of the ouput file
 * @param resize true if the image must be reduced
 * @param factorResize the image reduction factor 
 * @param extension the format of the slices to be processed, example: jp2
 * @return returns 0 if no problem encountered during image manipulation 
*/
int ToolsItk::stack2Dto3DParallV2(std::string inputDirectory,  int beginX, int endX, int beginY, int endY, int beginZ, int endZ, std::string output, bool resize, int factorResize, std::string extension) {
    std::cout << "omp_get_num_procs () = " << omp_get_num_procs() << std::endl;
    omp_set_num_threads(omp_get_num_procs()); // pour définir le nombre de threads voir si on rajoute un paramètre dans la fonction
    //std::cout << "number of threads = " << omp_get_num_threads() << std::endl;    
    std::vector<std::string> names ;
    std::vector<std::string> namesClean;
    using PixelType = unsigned int;  
    constexpr unsigned int InputImageDimension = 2;
    constexpr unsigned int OutputImageDimension = 3;    

    using InputImageType = itk::Image<PixelType, InputImageDimension>;
    using OutputImageType = itk::Image<PixelType, OutputImageDimension>;

    using ImageReaderType = itk::ImageFileReader<InputImageType>;

    using TilerType = itk::TileImageFilter<InputImageType, OutputImageType>;
  
    for (const auto & entry : std::filesystem::directory_iterator(inputDirectory))
        {  
        names.push_back(entry.path());      
        }
  
    std::sort(names.begin(), names.end()); // sort
  //std::vector<std::string>::iterator nit;  
  /*for (nit = names.begin(); nit != names.end(); ++nit)
  {
    std::cout << "File: " << (*nit).c_str() << std::endl;    
  }*/
    //std::cout << "names size = " << names.size() << std::endl;
    //std::cout << "names end = " << *(names.end()-1) << std::endl;  
    
    cleanList(names, namesClean, extension);
    //std::cout << "namesClean size = " << namesClean.size() << std::endl;
    if(namesClean.size() < (endZ-beginZ+1)) {
        std::cerr << "There are not enough files with extension " << extension << std::endl;
        return -1;
    }
    
    std::cout << "inputDirectory = " << inputDirectory << std::endl;
    std::cout << "factorResize = " << factorResize << std::endl;
    std::cout << "outputImage = " << output << std::endl;
    std::cout << "beginX = " << beginX << std::endl;
    std::cout << "endX = " << endX << std::endl;
    std::cout << "beginY = " << beginY << std::endl;
    std::cout << "endY = " << endY << std::endl;
    std::cout << "beginZ = " << beginZ << std::endl;
    std::cout << "endZ = " << endZ << std::endl;


    if(endZ > namesClean.size()-1) {
        std::cout << "The point can't be in the area, axis Z." << std::endl;
        return -1;
    } 

    /*for (int i=beginZ; i<endZ+1; i++)
    {
        std::cout << "File: " << namesClean.at(i) << std::endl;    
    }*/
 
    // créer une image de taille (endX-beginX+1, endY-beginY+1, endZ-beginZ+1)
    ImageType3D::Pointer imageOutput;
    imageOutput = ImageType3D::New();
    ImageType3D::IndexType cornerOutput = { { 0, 0 , 0} };
    ImageType3D::SizeType sizeOutput;
    unsigned int nbRows = 0;
    unsigned int nbCols = 0;
    unsigned int nbSlices = 0;    
    
    if(beginX != -1 && beginY != -1 && factorResize == 1) { // case ROI
        std::cout << "case ROI" << std::endl;
        nbRows = endY-beginY+1;
        nbCols = endX-beginX+1;
        nbSlices = endZ-beginZ+1;
    } else if(beginX == -1 && beginY == -1) { // case resize with factorResize        
        ImageType2D::Pointer imageTemp = itk::ReadImage<ImageType2D>(namesClean.at(0));
        ImageType2D::RegionType regionTemp = imageTemp->GetLargestPossibleRegion();
        ImageType2D::SizeType sizeTemp;
        sizeTemp = regionTemp.GetSize();
        std::cout << "sizeTemp = " << sizeTemp << std::endl;
        if(resize) { // case resize with factorResize
            std::cout << "case resize Image" << std::endl;
            nbRows = sizeTemp[1]/factorResize+1;
            nbCols = sizeTemp[0]/factorResize+1;
            nbSlices = (endZ-beginZ+1)/factorResize+1;
        } else { // stack  without resize
            std::cout << "stack without resize" << std::endl;
            nbRows = sizeTemp[1];
            nbCols = sizeTemp[0];
            nbSlices = endZ-beginZ+1;
        }        
    }    
    
    std::cout << "nbRows = " << nbRows << std::endl;
    std::cout << "nbCols = " << nbCols << std::endl;
    std::cout << "nbSlices = " << nbSlices << std::endl;
    sizeOutput[0] = nbCols;
    sizeOutput[1] = nbRows;
    sizeOutput[2] = nbSlices;    
    //std::cout << "x sizeNew[0] = " << sizeNew[0] << std::endl;
    //std::cout << "y sizeNew[1] = " << sizeNew[1] << std::endl;
    //std::cout << "minY = " << minY << std::endl;
    //std::cout << "maxY = " << maxY << std::endl;
    //std::cout << "minX = " << minX << std::endl;
    //std::cout << "maxX = " << maxX << std::endl;
    std::cout << "cornerOutput = " << cornerOutput << std::endl;
    std::cout << "sizeOutput = " << sizeOutput << std::endl;
    ImageType3D::RegionType regionOutput(cornerOutput, sizeOutput);    
    imageOutput->SetRegions(regionOutput);    
    imageOutput->Allocate();
    ImageType3D::IndexType indexOutput;
    /*uint cpty =0;
    uint cptx =0;    
    for(int y=minY; y<maxY; y= y+factorResize) { 
      indexOrigin[1]= y;
      cptx=0;          
      for(int x=minX; x<maxX; x= x+factorResize) { 
        indexOrigin[0]= x;        
        indexNew[1] = cpty;
        indexNew[0] = cptx;
        //std::cout << "(" << indexOrigin[1]  <<  ", " << indexOrigin[0] << ") -> (" << indexNew[1]  <<  ", " << indexNew[0] << ")"  << std::endl;        
        imageNew->SetPixel(indexNew, imageOrigin->GetPixel(indexOrigin));            
        cptx++;              
      }
      cpty++;
    }  */  
   

    auto reader = ImageReaderType::New();

    InputImageType::Pointer inputImageTile;
    InputImageType::RegionType region;
    int cpt =0;

    //std::vector<ImageType2D::Pointer> tabImages((endZ-beginZ+1)/factorResize+1);
    std::vector<int> tabIndex((endZ-beginZ+1)/factorResize+1);
    //std::cout << "tabImages size = " << tabImages.size() << std::endl;
    std::cout << "tabIndex size = " << tabIndex.size() << std::endl;
    /*for(uint i=0; i<tabImages.size(); i++ ) {
        tabImages[i] = NULL;
    }*/
    for(uint i=0; i<tabIndex.size(); i++ ) {
        tabIndex[i] = 0;
    }
    int th_id, nthreads;
    int stack =-1;
    std::chrono::duration<double> duration_load;
    double totalTimeLoad = 0;
    std::chrono::duration<double> duration_changeSizeImage;
    double totalTimeChangeSizeImage = 0;
    std::chrono::duration<double> duration_stack;
    double totalStack = 0;
    std::chrono::duration<double> duration_write;
    double totalWrite = 0;
    std::chrono::duration<double> duration_write_image;
    double totalWriteImage = 0;
    
    #pragma omp parallel for shared(stack) private(th_id) schedule(dynamic, 4)
    for (int i=beginZ; i<endZ+1; i= i +factorResize)
    {            
        th_id = omp_get_thread_num();
        auto start_timeLoad = std::chrono::high_resolution_clock::now();          
        ImageType2D::Pointer image = itk::ReadImage<ImageType2D>(namesClean.at(i));
        auto end_timeLoad = std::chrono::high_resolution_clock::now();
        duration_load = end_timeLoad - start_timeLoad;
        totalTimeLoad += duration_load.count();
        ImageType2D::Pointer imageNew;
        imageNew = ImageType2D::New();
        if (resize) {
            
            auto start_changeSizeImage = std::chrono::high_resolution_clock::now();             
            int res = changeSizeImage(image, imageNew, factorResize, beginX, endX, beginY, endY);
            auto end_changeSizeImage = std::chrono::high_resolution_clock::now();
            duration_changeSizeImage = end_changeSizeImage - start_changeSizeImage;
            totalTimeChangeSizeImage +=  duration_changeSizeImage.count();
            //tabImages[(i-beginZ)/factorResize] = imageNew;
        
        } else {
            //tabImages[i-beginZ] = image; 
            imageNew = image;               
        }
            auto start_writeImage = std::chrono::high_resolution_clock::now();
            uint cpty =0;
            uint cptx =0;
            ImageType3D::IndexType indexOutput;
            ImageType2D::IndexType indexImageNew;
            uint sizeXImageNew = nbCols;
            uint sizeYImageNew = nbRows;
            // voir si on peut remplacer par un iterator   
            /*for(int y=0; y<sizeYImageNew; y++) { 
                indexImageNew[1]= y;
                cptx=0;          
                for(int x=0; x<sizeXImageNew; x++) { 
                    indexImageNew[0]= x;        
                    indexOutput[1] = cpty;
                    indexOutput[0] = cptx;
                    indexOutput[2] = i/factorResize;                    
                    //printf("i = %d sizeXImageNew = %d sizeYImageNew = %d (%ld, %ld ) -> (%ld, %ld, %ld)\n" , i, sizeXImageNew, sizeYImageNew, indexImageNew[0], indexImageNew[1], indexOutput[0], indexOutput[1], indexOutput[2]);        
                    imageOutput->SetPixel(indexOutput, imageNew->GetPixel(indexImageNew));            
                    cptx++;              
                }
                cpty++;
            }*/
            constexpr unsigned int Dimension2D = 2;
            constexpr unsigned int Dimension3D = 3;
            using PixelType = unsigned int;
            using ImageType2D = itk::Image<PixelType, Dimension2D>;
            using ImageType3D = itk::Image<PixelType, Dimension3D>;
            using ConstIteratorType = itk::ImageRegionConstIterator<ImageType2D>;
            using IteratorType = itk::ImageRegionIterator<ImageType3D>;
            ImageType2D::RegionType inputRegion;
            ImageType2D::RegionType::IndexType inputStart;
            ImageType2D::RegionType::SizeType inputSize;
            inputStart[0] = 0;
            inputStart[1] = 0;
            inputSize[0] = sizeXImageNew;
            inputSize[1] = sizeYImageNew;
            inputRegion.SetSize(inputSize);
            inputRegion.SetIndex(inputStart);
            ImageType3D::RegionType outputRegion;
            ImageType3D::RegionType::IndexType outputStart;
            ImageType3D::RegionType::SizeType outputSize;
            outputStart[0] = 0;
            outputStart[1] = 0;
            outputStart[2] = i/factorResize;
            outputSize[0] = sizeXImageNew;
            outputSize[1] = sizeYImageNew;
            outputSize[2] = 1;
            outputRegion.SetSize(outputSize);
            outputRegion.SetIndex(outputStart);
            ConstIteratorType inputIt(imageNew, inputRegion);
            IteratorType outputIt(imageOutput, outputRegion);
            inputIt.GoToBegin();
            outputIt.GoToBegin();
            while (!inputIt.IsAtEnd())
            {
                outputIt.Set(inputIt.Get());
                ++inputIt;
                ++outputIt;
            }


            auto end_writeImage = std::chrono::high_resolution_clock::now();
            duration_write_image = end_writeImage - start_writeImage;
            totalWriteImage +=  duration_write_image.count();

        
            
        tabIndex[(i-beginZ)/factorResize] = 1;
            printf("Hello World from thread %d i = %d imod = %d stack = %d\n", th_id, i, (i-beginZ)/factorResize, stack);
            std::cout << "tabIndex : ";
            for(uint i=0; i<tabIndex.size(); i++ ) {
                std::cout << tabIndex[i] << " ";
            }
            std::cout << std::endl;          
        //#pragma omp critical
        //{
        //auto start_stack = std::chrono::high_resolution_clock::now();
        //while(tabIndex[stack+1] == 1) {
            //std::cout << namesClean.at((stack+1)*factorResize+beginZ) << std::endl;                
            //tiler->SetInput(inputImageNumber++, tabImages[stack+1]);   
            //tabImages[stack+1] = NULL;
            //tabIndex[stack+1] = -1;
            //stack++;                
        //}
        //auto end_stack = std::chrono::high_resolution_clock::now();
        //duration_stack = end_stack - start_stack;
        //totalStack +=  duration_stack.count(); 
        //}



        cpt++;
    }
    std::cout << "Time load mean = " << totalTimeLoad/((endZ-beginZ+1)/factorResize) << std::endl;
    std::cout << "Time changeSizeImage mean = " << totalTimeChangeSizeImage/((endZ-beginZ+1)/factorResize) << std::endl;
    std::cout << "Time write Image mean = " << totalWriteImage/((endZ-beginZ+1)/factorResize) << std::endl; 
    //std::cout << "Time stack mean = " << totalStack/(endZ-beginZ+1) << std::endl;
    
    std::cout << "tabIndex final: ";
    for(uint i=0; i<tabIndex.size(); i++ ) {
        std::cout << tabIndex[i] << " ";
    }
    std::cout << std::endl;   
     
    //std::cout << "inputImageNumber = " << inputImageNumber << std::endl; 
    auto start_write = std::chrono::high_resolution_clock::now();
    /*PixelType filler = 128;

    tiler->SetDefaultPixelValue(filler);

    tiler->Update();*/
    
    try
    {
        itk::WriteImage(imageOutput, output);
    }
    catch (const itk::ExceptionObject & excp)
    {
        std::cerr << excp << std::endl;
        return EXIT_FAILURE;
    }
    auto end_write = std::chrono::high_resolution_clock::now();
    duration_write = end_write - start_write;
    totalWrite +=  duration_write.count();
    std::cout << "Time write final= " << totalWrite << std::endl; 
    return 0;  
}

/** 
 * @brief compute the density profile
 * 
 * @param x the x coordinate of the origin point
 * @param y the y coordinate of the origin point
 * @param z the z coordinate of the origin point
 * @param vectorX the x coordinate of the direction vector
 * @param vectorY the y coordinate of the direction vector
 * @param vectorZ the z coordinate of the direction vector
 * @param nbpoints the number of points to be taken into account for calculating the profile
 * @param inputDirectory the directory that contains all the slices
 * @param outputFilename the name of the ouput file
 * @param inputFile the name of the input file
 * @param distanceNeighbors the neighborhood distance
 * @param measurement the nature of the  statistical instrument, m for mean, d for median, n for min, x for max
 * @param typeBlock the shape of the neighborhood, 3 for a 3D block, 2 for an orthogonal plan 
 * @return returns 0 if no problem encountered during image manipulation 
*/
int ToolsItk::computeProfile(int x, int y, int z, double vectorX, double vectorY, double vectorZ, int nbpoints, std::string outputFilename, std::string inputFile, int distanceNeighbors, char measurement, int typeBlock) {
    IndexType3D index3D;    
    ImageType3D::Pointer image3D;    

    std::chrono::duration<double> duration_load;
    double totalTimeLoad = 0;    
    int nvPx = 0;
    int nvPy = 0;
    int nvPz = 0;
    int valPixel = 0;
    int tab[nbpoints];
    std::ofstream outP(outputFilename);

    double vector[3];
    double baseVector1[3] = {0,0,0};
    double baseVector2[3] = {0,0,0};
    vector[0] = vectorX;
    vector[1] = vectorY;
    vector[2] = vectorZ;   
    
    std::cout << "load file = " << inputFile << std::endl;
    image3D = itk::ReadImage<ImageType3D>(inputFile);

    if(typeBlock == 2) {
        computeBaseVector(vector, baseVector1,  baseVector2);
    }


    for (int k=0; k<nbpoints; k++)
    {            
        nvPx = static_cast<int>(round(x + k * vectorX));
        nvPy = static_cast<int>(round(y + k * vectorY));
        nvPz = static_cast<int>(round(z + k * vectorZ));               
        auto start_timeLoad = std::chrono::high_resolution_clock::now();          
        index3D[0]= nvPx;
        index3D[1]= nvPy;
        index3D[2]= nvPz;
        if(distanceNeighbors>0) {                
            valPixel = computeMeasurement(nvPx, nvPy, nvPz, baseVector1, baseVector2, distanceNeighbors, image3D, measurement, typeBlock);
        } else {
            valPixel = image3D->GetPixel(index3D);
        }            
        //std::cout << "valPixel = " << valPixel << std::endl ;        
        tab[k] = valPixel;
    }
    
    for(int k=0; k<nbpoints; k++) {
        nvPx = static_cast<int>(round(x + k * vectorX));
        nvPy = static_cast<int>(round(y + k * vectorY));
        nvPz = static_cast<int>(round(z + k * vectorZ));
        outP << nvPx << " " << nvPy << " " << nvPz << " " << tab[k]  << std::endl;
        //std::cout << "k " << k << " " << tab[k] << std::endl; 
    }
    outP.close();
    std::cout << "Time load mean = " << totalTimeLoad/nbpoints << std::endl;    
    
    return 0;

}

/** 
 * @brief call a python program to  display the density profile
 * 
 * @param filename the name of the file that contains the profile data 
 * @return returns 0 if no problem encountered during image manipulation 
*/
int ToolsItk::displayProfile(std::string filename) {
    std::string command = "python3 displayProfile.py " + filename;
    std::cout << command << std::endl;
    int result = system(command.c_str());

    if (result != 0) {
        std::cerr << "Error with python3 displayProfile.py " + filename  << std::endl;
        return 1;
    }    

    return 0;
}

/** 
 * @brief computes the values ​​of the voxels of the neighbors of the origin point according to a neighborhood distance
 * 
 * @param px  the x coordinate of the origin point
 * @param py  the y coordinate of the origin point
 * @param pz  the z coordinate of the origin point
 * @param distance the distance between the origin point and the edge of the cube
 * @param image the pointer to the image
 * @param tab it contains the voxel values, tab is sorted at the end 
 * @return returns 0 if no problem encountered during image manipulation 
*/
int ToolsItk::listOfValuesFromNeighbors(int px, int py, int pz, int distance, ImageType3D::Pointer image,  std::vector<uint> &tab) {
    int minX = px-distance;
    int maxX = px+distance;
    int minY = py-distance;
    int maxY = py+distance;
    int minZ = pz-distance;
    int maxZ = pz+distance;   
    IndexType3D index3D;    

    for(int z=minZ; z<maxZ+1; z++) {        
        for(int y=minY; y<maxY+1; y++) {             
            for(int x=minX; x<maxX+1; x++) {                
                index3D[0] = x;
                index3D[1] = y;
                index3D[2] = z;
                tab.push_back(image->GetPixel(index3D));
            }                             
        }
    }

    std::sort(tab.begin(), tab.end()); // sort 
    //std::cout << "listOfValuesFromNeighbors tab.size() = " << tab.size() << std::endl;   
    return 0;
}

/** 
 * @brief computes the values ​​of the voxels of the neighbors of the origin point according to a neighborhood distance and an orthogonal plan
 * 
 * @param px  the x coordinate of the origin point
 * @param py  the y coordinate of the origin point
 * @param pz  the z coordinate of the origin point
 * @param baseVector1 the coordinates of the first base vector of the orthogonal plane
 * @param baseVector2 the coordinates of the second base vector of the orthogonal plane
 * @param distance the distance before and after the origin point 
 * @param image the pointer to the image
 * @param tab it contains the voxel values, tab is sorted at the end 
 * @return returns 0 if no problem encountered during image manipulation 
*/
int ToolsItk::listOfValuesFromNeighbors2D(int px, int py, int pz, double baseVector1[], double baseVector2[], int distance, ImageType3D::Pointer image, std::vector<uint> &tab) {
    IndexType3D index3D;
    int valPixel = 0;
    int nvPx = 0;
    int nvPy = 0;
    int nvPz = 0;    
    
    for(int k1=-distance; k1<distance+1; k1++) {
        for(int k2=-distance; k2<distance+1; k2++) {
            nvPx = static_cast<int>(round(px + k1 * baseVector1[0] + k2 * baseVector2[0]));
            nvPy = static_cast<int>(round(py + k1 * baseVector1[1] + k2 * baseVector2[1]));
            nvPz = static_cast<int>(round(pz + k1 * baseVector1[2] + k2 * baseVector2[2]));
            index3D[0] = nvPx;
            index3D[1] = nvPy;
            index3D[2] = nvPz;
            tab.push_back(image->GetPixel(index3D));
        }
    }

    std::sort(tab.begin(), tab.end()); // sort 
    //std::cout << "listOfValuesFromNeighbors tab.size() = " << tab.size() << std::endl;   
    return 0;
}


/** 
 * @brief computes a statistical measure for a given voxel
 * 
 * @param px  the x coordinate of the origin point
 * @param py  the y coordinate of the origin point
 * @param pz  the z coordinate of the origin point
 * @param baseVector1 the coordinates of the first base vector of the orthogonal plane
 * @param baseVector2 the coordinates of the second base vector of the orthogonal plane
 * @param distance the distance before and after the origin point 
 * @param image the pointer to the image
 * @param measurement the nature of the  statistical instrument, m for mean, d for median, n for min, x for max
 * @param dimension the shape of the neighborhood, 3 for a 3D block, 2 for an orthogonal plan 
 * @return returns the value for the voxel 
*/
int ToolsItk::computeMeasurement(int px, int py, int pz, double baseVector1[], double baseVector2[], int distance, ImageType3D::Pointer image, char measurement, int dimension) {
    int valPixel = 0;
    IndexType3D index3D;
    uint size =0;    
    std::vector<uint> tab;    

    if(dimension == 3) {
        listOfValuesFromNeighbors(px, py, pz, distance, image, tab);
    } else {
        listOfValuesFromNeighbors2D(px, py, pz, baseVector1, baseVector2, distance, image, tab);
    }
    
    switch(measurement) {
        case 'm': // mean            
            valPixel = computeDistanceMean(tab);  
            break;        
        case 'd': // median            
            valPixel = computeDistanceMedian(tab);              
            break;
        case 'n': // min           
            valPixel = computeDistanceMin(tab);  
            break;        
        case 'x': // max            
            valPixel = computeDistanceMax(tab);              
            break;
        default:
            valPixel = 0;
            std::cout << "Problem with the value of measurement!" << std::endl;
    }
    return valPixel;
}

/** 
 * @brief computes the mean from a set of voxel level values
 * 
 * @param tab it contains the voxel values
 * @return returns the value for the voxel 
*/
int ToolsItk::computeDistanceMean(std::vector<uint> tab) {    
    int somme = 0;
    double moy = 0.0;    
    int valPixel = 0;
    int size =0;
    size = tab.size();

    for(int i=0; i<size; i++) {
        somme += tab[i];
    }
    
    moy = somme/size;    
    valPixel = int(moy);    
    return valPixel;
}

/** 
 * @brief computes the median from a set of voxel level values
 * 
 * @param tab it contains the voxel values
 * @return returns the value for the voxel 
*/
int ToolsItk::computeDistanceMedian(std::vector<uint> tab) {
    uint middle = tab.size()/2; 
    int valPixel = tab[middle] ;
    return valPixel;
}

/** 
 * @brief computes the min from a set of voxel level values
 * 
 * @param tab it contains the voxel values
 * @return returns the value for the voxel 
*/
int ToolsItk::computeDistanceMin(std::vector<uint> tab) {
    //uint min = *std::min_element(tab.begin(), tab.end());
    uint min = tab[0];
    return min;
}

/** 
 * @brief computes the max from a set of voxel level values
 * 
 * @param tab it contains the voxel values
 * @return returns the value for the voxel 
*/
int ToolsItk::computeDistanceMax(std::vector<uint> tab) {   
    uint max = tab[tab.size()-1];
    return max;
}


/** 
 * @brief computes the basis vectors of the orthogonal plane to a direction vector
 * 
 * @param vector1 the coordinates of the direction vector
 * @param baseVector1 the coordinates of the first base vector of the orthogonal plane
 * @param baseVector2 the coordinates of the second base vector of the orthogonal plane 
 * @return returns the value for the voxel 
*/
int ToolsItk::computeBaseVector(double vector[], double * baseVector1,  double * baseVector2) {
    baseVector1[0] = 0;
    baseVector1[1] = 1;
    if(vector[2]!= 0) baseVector1[2] = -1.0 * vector[1]/vector[2];    
    double norm1 = sqrt(baseVector1[0]* baseVector1[0] + baseVector1[1]* baseVector1[1] + baseVector1[2]* baseVector1[2]);    
    baseVector1[0] = baseVector1[0]/norm1;
    baseVector1[1] = baseVector1[1]/norm1;
    baseVector1[2] = baseVector1[2]/norm1;
    baseVector2[0] = 1;
    baseVector2[1] = 0;
    if(vector[2]!= 0) baseVector2[2] =  -1.0 *  vector[0]/vector[2];    
    double norm2 = sqrt(baseVector2[0]* baseVector2[0] + baseVector2[1]* baseVector2[1] + baseVector2[2]* baseVector2[2]);    
    baseVector2[0] = baseVector2[0]/norm2;
    baseVector2[1] = baseVector2[1]/norm2;
    baseVector2[2] = baseVector2[2]/norm2;
    std::cout << "computeBaseVector vector = (" << vector[0] << ", " << vector[1] << ", " << vector[2] << ")" << std::endl;
    std::cout << "computeBaseVector baseVector1 = (" << baseVector1[0] << ", " << baseVector1[1] << ", " << baseVector1[2] << ")" << std::endl;
    std::cout << "computeBaseVector baseVector2 = (" << baseVector2[0] << ", " << baseVector2[1] << ", " << baseVector2[2] << ")" << std::endl;
    return 0;
}


