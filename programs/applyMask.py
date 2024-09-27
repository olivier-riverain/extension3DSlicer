import sys, os
import numpy as np
import cv2

print("applyMask")
#  python3 applyMask.py ~/home/olivier/m2/stage/images/43.67um_pomelos1_pag-0.08_0.24_jp2_ ~/home/olivier/m2/stage/images/mask_pomelo1

if len( sys.argv ) < 4:    
    print( "\tusage: python3 applyMask.py inputDirectoryImage inputDirectoryMask outputDirectory" )
    exit()


inputDirectoryImage = sys.argv[1]
print("inputDirectoryImage = ", inputDirectoryImage)
inputDirectoryMask = sys.argv[2]
print("inputDirectoryMask = ", inputDirectoryMask)
outputDirectory = sys.argv[3]
print("outputDirectory = ", outputDirectory)

dirImage = os.listdir(inputDirectoryImage)
dirImage.sort()
dirMask = os.listdir(inputDirectoryMask)
dirMask.sort()
lendirMask = len(dirMask)

print("len(dirImage)= ", len(dirImage))
print("len(dirMask)= ", len(dirMask))

def countPixels(mask):
    countZero = 0
    countOne =0
    for y in range(len(mask)):
        for x in range(len(mask[0])):
            if mask[y,x] == 0:
                countZero = countZero +1
            if mask[y,x] == 1:
                countOne = countOne +1
    return countZero, countOne


for i in range(3216,3230):
#for i in range(lendirMask):   
    print("i = ", i)
    print(dirImage[i])
    print(dirMask[i])
    mask = np.load(inputDirectoryMask + "/" + dirMask[i]) # TODO vérifier si termine par "/"" ou pas
    print("len(mask) = ", len(mask))
    print("len(mask[0]) = ", len(mask[0]))
    #print("dtype = ", mask.dtype)
    #print("shape = ", mask.shape) #(y,x)    
    #countZero, countOne = countPixels(mask)
    #print("countZero = ", countZero, " countOne = ", countOne)
    #print("total pixel = ", countZero + countOne)
    #print("inputDirectoryImage + / + dirImage[i] = ", inputDirectoryImage + "/" + dirImage[i])
    inputImg = cv2.imread(inputDirectoryImage + "/" + dirImage[i], cv2.IMREAD_UNCHANGED)
    #print("dtype inputImg= ", inputImg.dtype)
    #print("type(inputImg) = ", type(inputImg))
    #print("inputImg shape = ", inputImg.shape[:3])
    inputImg[mask[:,:] == 0] = 0
    outputFilename = outputDirectory + "/" + dirImage[i]
    print("outputFilename = ", outputFilename)
    cv2.imwrite(outputFilename, inputImg)
    


