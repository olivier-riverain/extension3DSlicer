import logging
import os
from typing import Annotated, Optional

import vtk

import slicer
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
)

from slicer import vtkMRMLScalarVolumeNode

# begin olivier
'''try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    slicer.util.pip_install("matplotlib")
    import matplotlib.pyplot as plt'''

import numpy as np
import SimpleITK as sitk
import sitkUtils
import subprocess
import qt
import json
import math
#from pylab import *
import shutil

# end Olivier

#
# t_ZoomRoi
#


class t_ZoomRoi(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("t_ZoomRoi")  # TODO: make this more human readable by adding spaces
        # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Citrus Skin")]
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["Olivier Riverain (LaBRI I2M).)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        # _() function marks text as translatable to other languages
        self.parent.helpText = _("""
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#t_ZoomRoi">module documentation</a>.
""")
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = _("""
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""")

        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", registerSampleData)


#
# Register sample data sets in Sample Data module
#


def registerSampleData():
    """Add data sets to Sample Data module."""
    # It is always recommended to provide sample data for users to make it easy to try the module,
    # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

    import SampleData

    iconsPath = os.path.join(os.path.dirname(__file__), "Resources/Icons")

    # To ensure that the source code repository remains small (can be downloaded and installed quickly)
    # it is recommended to store data sets that are larger than a few MB in a Github release.

    # t_ZoomRoi1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="t_ZoomRoi",
        sampleName="t_ZoomRoi1",
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, "t_ZoomRoi1.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames="t_ZoomRoi1.nrrd",
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums="SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        # This node name will be used when the data set is loaded
        nodeNames="t_ZoomRoi1",
    )

    # t_ZoomRoi2
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="t_ZoomRoi",
        sampleName="t_ZoomRoi2",
        thumbnailFileName=os.path.join(iconsPath, "t_ZoomRoi2.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames="t_ZoomRoi2.nrrd",
        checksums="SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        # This node name will be used when the data set is loaded
        nodeNames="t_ZoomRoi2",
    )


#
# t_ZoomRoiParameterNode
#


@parameterNodeWrapper
class t_ZoomRoiParameterNode:
    """
    The parameters needed by module.

    inputVolume - The volume to threshold.
    imageThreshold - The value at which to threshold the input volume.
    invertThreshold - If true, will invert the threshold.
    thresholdedVolume - The output volume that will contain the thresholded volume.
    invertedVolume - The output volume that will contain the inverted thresholded volume.
    """

    inputVolume: vtkMRMLScalarVolumeNode
    imageThreshold: Annotated[float, WithinRange(0, 2**16-1)] = 100
    invertThreshold: bool = False
    thresholdedVolume: vtkMRMLScalarVolumeNode
    invertedVolume: vtkMRMLScalarVolumeNode


#
# t_ZoomRoiWidget
#


class t_ZoomRoiWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        print("--------------------------")
        print("__init__ begin")
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._parameterNodeGuiTag = None        
        self._updatingGUIFromParameterNode = False
        self.pointX = None
        self.pointY = None
        self.pointZ = None
        self.sizeX = None
        self.sizeY = None
        self.sizeZ = None
        self.radioButtonNoLink = None
        self.radioButtonSquare = None
        self.radioButtonCube = None
        self.radioButtonFile = None
        self.radioButtonDirectory = None
        print("__init__ end")

    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        print("setup begin")
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/t_ZoomRoi.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = t_ZoomRoiLogic()

        # begin code Olivier        
        # ROI markups
        self.markupsNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsROINode")
        self.markupsNodeId = self.markupsNode.GetID()
        self.markupsNode.CreateDefaultDisplayNodes()
        print("self.markupsNode.GetDisplayNode().GetSelectedColor() = ", self.markupsNode.GetDisplayNode().GetSelectedColor()) 
        self.markupsNode.GetDisplayNode().SetSelectedColor(0.0,0.0,1.0)
        print("self.markupsNode.GetDisplayNode().GetSelectedColor() bleu = ", self.markupsNode.GetDisplayNode().GetSelectedColor())
        self.markupsNode.GetDisplayNode().SetPointLabelsVisibility(True)
        self.markupsNode.GetDisplayNode().SetVisibility(True)
        self.ui.roiMarkupsPlaceWidget.setMRMLScene(slicer.mrmlScene)
        self.ui.roiMarkupsPlaceWidget.setCurrentNode(slicer.mrmlScene.GetNodeByID(self.markupsNodeId))
        print("setup self.markupsNode.GetID() = ", self.markupsNodeId)
        self.ui.roiMarkupsPlaceWidget.buttonsVisible=True # pour l'instant,  décommenter les lignes suivantes après
        #self.ui.roiMarkupsPlaceWidget.buttonsVisible=False
        #self.ui.roiMarkupsPlaceWidget.placeButton().show()
        #self.ui.roiMarkupsPlaceWidget.deleteButton().show()
        
        # Profile markups
        self.profileMarkupsNodeOrigin = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsROINode")
        self.profileMarkupsNodeIdOrigin = self.profileMarkupsNodeOrigin.GetID()
        self.profileMarkupsNodeOrigin.CreateDefaultDisplayNodes()
        print("self.profileMarkupsNodeOrigin.GetDisplayNode().GetSelectedColor() = ", self.profileMarkupsNodeOrigin.GetDisplayNode().GetSelectedColor()) 
        self.profileMarkupsNodeOrigin.GetDisplayNode().SetSelectedColor(0.0,1.0,0.0)
        print("self.profileMarkupsNodeOrigin.GetDisplayNode().GetSelectedColor() vert = ", self.profileMarkupsNodeOrigin.GetDisplayNode().GetSelectedColor())
        self.profileMarkupsNodeOrigin.GetDisplayNode().SetPointLabelsVisibility(True)
        self.profileMarkupsNodeOrigin.GetDisplayNode().SetVisibility(True)
        self.ui.profileMarkupsPlaceWidgetOrigin.setMRMLScene(slicer.mrmlScene)
        self.ui.profileMarkupsPlaceWidgetOrigin.setCurrentNode(slicer.mrmlScene.GetNodeByID(self.profileMarkupsNodeIdOrigin))
        print("setup self.profileMarkupsNodeOrigin.GetID() = ", self.profileMarkupsNodeIdOrigin)
        self.ui.profileMarkupsPlaceWidgetOrigin.buttonsVisible=True
        
        self.profileMarkupsNodeDestination = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsROINode")
        self.profileMarkupsNodeIdDestination = self.profileMarkupsNodeDestination.GetID()
        self.profileMarkupsNodeDestination.CreateDefaultDisplayNodes()
        print("self.profileMarkupsNodeDestination.GetDisplayNode().GetSelectedColor() = ", self.profileMarkupsNodeDestination.GetDisplayNode().GetSelectedColor()) 
        self.profileMarkupsNodeDestination.GetDisplayNode().SetSelectedColor(0.0,1.0,1.0)
        print("self.profileMarkupsNodeDestination.GetDisplayNode().GetSelectedColor() vert = ", self.profileMarkupsNodeDestination.GetDisplayNode().GetSelectedColor())
        self.profileMarkupsNodeDestination.GetDisplayNode().SetPointLabelsVisibility(True)
        self.profileMarkupsNodeDestination.GetDisplayNode().SetVisibility(True)
        self.ui.profileMarkupsPlaceWidgetDestination.setMRMLScene(slicer.mrmlScene)
        self.ui.profileMarkupsPlaceWidgetDestination.setCurrentNode(slicer.mrmlScene.GetNodeByID(self.profileMarkupsNodeIdDestination))
        print("setup self.profileMarkupsNodeDestination.GetID() = ", self.profileMarkupsNodeIdDestination)
        self.ui.profileMarkupsPlaceWidgetDestination.buttonsVisible=True



        self.ui.radioButtonNoLink.setChecked(True)
        self.logic.shape = "n"
        self.ui.checkBoxZoom.checked = False        
        
        self.logic.loadConfiguration()
        self.logic.saveJsonDirectory = self.logic.createDirectory(self.logic.directoryConfig + "/" + "saveParam/", self.logic.saveJsonDirectory)
        self.logic.eraseFilesJson(self.logic.saveJsonDirectory)
        print("setup self.logic.saveJsonDirectory = ", self.logic.saveJsonDirectory )
        self.logic.directoryTemp = self.logic.createDirectory(self.logic.directoryConfig + "/" + "saveParam/temp/", self.logic.directoryTemp)
        self.logic.eraseFilesTmp(self.logic.directoryTemp)
        print("setup self.logic.directoryTemp = ", self.logic.directoryTemp)       
        print("setup self.logic.programDirectory = ", self.logic.programDirectory)
        if self.logic.programDirectory !=  None:
            self.ui.programDirectoryPathLineEdit.setCurrentPath(self.logic.programDirectory)      
        
       
        # end code Olivier

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)
        
        # begin code Olivier        
        self.ui.inputVolumeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
        self.ui.buttonCreateROI.connect("clicked(bool)", self.onCreateROIButton)
        self.ui.buttonResize.connect("clicked(bool)", self.onResizeButton)
        self.ui.buttonZoom.connect("clicked(bool)", self.onZoomButton)
        self.ui.buttonProfile.connect("clicked(bool)", self.onProfileButton)
        self.ui.buttonDisplayProfile.connect("clicked(bool)", self.onDisplayProfileButton)        
        self.ui.buttonOpenFile.connect("clicked(bool)", self.onOpenFileButton)
        self.ui.buttonSaveImageProfile.connect("clicked(bool)", self.onSaveImageProfile)               
        self.addObserver(self.markupsNode, slicer.vtkMRMLMarkupsNode.PointModifiedEvent, self.onPointModifiedEvent)
        self.ui.inputFilePathLineEdit.currentPathChanged.connect(self.onInputFilePathLineEditChanged)
        self.ui.inputDirectoryPathLineEdit.connect('currentPathChanged(const QString&)', self.onInputDirectoryPathLineEditChanged)
        self.ui.programDirectoryPathLineEdit.connect('currentPathChanged(const QString&)', self.onProgramDirectoryPathLineEditChanged)
        #self.ui.editPointX.textEdited.connect(self.editPointXChanged) # TODO compute the matrix IJK to RAS
        #self.ui.editPointY.textEdited.connect(self.editPointYChanged)
        #self.ui.editPointZ.textEdited.connect(self.editPointZChanged)   
        self.ui.editSizeX.textEdited.connect(self.editSizeXChanged)
        self.ui.editSizeY.textEdited.connect(self.editSizeYChanged)
        self.ui.editSizeZ.textEdited.connect(self.editSizeZChanged)
        self.ui.editSizeZ.textEdited.connect(self.editSizeZChanged)         
        self.ui.radioButtonNoLink.toggled.connect(self.onradioButtonNoLink)
        self.ui.radioButtonSquare.toggled.connect(self.onradioButtonSquare)
        self.ui.radioButtonCube.toggled.connect(self.onradioButtonCube)
        self.ui.radioButtonFile.toggled.connect(self.onradioButtonFile)
        self.ui.radioButtonDirectory.toggled.connect(self.onradioButtonDirectory)        
        self.ui.outputFilePathLineEdit.currentPathChanged.connect(self.onOutputFilePathLineEditChanged)
        self.ui.RangeWidgetSlices.valuesChanged.connect(self.onRangeWidgetSlicesChanged)
        self.ui.PathLineEditOutputfileResized.currentPathChanged.connect(self.onResizedOutputFilePathLineEditChanged)
        self.ui.SliderWidgetFactorResize.valueChanged.connect(self.onSliderWidgetFactorResizeChanged)
        self.ui.checkBoxZoom.toggled.connect(self.onCheckBoxZoomChanged)
        self.ui.comboBoxZoom1.currentTextChanged.connect(self.onComboBoxZoom1Changed)
        self.ui.comboBoxZoom2.currentTextChanged.connect(self.onComboBoxZoom2Changed)        
        self.addObserver(self.profileMarkupsNodeOrigin, slicer.vtkMRMLMarkupsNode.PointModifiedEvent, self.onProfilePointModifiedEventOrigin)
        self.addObserver(self.profileMarkupsNodeDestination, slicer.vtkMRMLMarkupsNode.PointModifiedEvent, self.onProfilePointModifiedEventDestination)
        self.ui.SliderWidgetNeighbor.valueChanged.connect(self.onSliderWidgetNeighborChanged)
        self.ui.SliderWidgetSteps.valueChanged.connect(self.onSliderWidgetStepChanged)
        self.ui.profileOutputFilePathLineEdit.currentPathChanged.connect(self.onProfileOutputFilePathLineEditChanged)
        self.ui.profileFilePathLineEdit.currentPathChanged.connect(self.onProfileFilePathLineEditChanged)
        #self.ui.radioButtonProfileFile.toggled.connect(self.onradioButtonProfileFile)
        #self.ui.radioButtonProfileDirectory.toggled.connect(self.onradioButtonProfileDirectory)
        self.ui.radioButtonProfileNormal.toggled.connect(self.onradioButtonProfileNormal)
        self.ui.radioButtonProfileDirection.toggled.connect(self.onradioButtonProfileDirection)
        self.ui.radioButtonProfileMean.toggled.connect(self.onradioButtonProfileMean)
        self.ui.radioButtonProfileMedian.toggled.connect(self.onradioButtonProfileMedian)
        self.ui.radioButtonProfileMin.toggled.connect(self.onradioButtonProfileMin)
        self.ui.radioButtonProfileMax.toggled.connect(self.onradioButtonProfileMax)
        self.ui.radioButtonProfileBlock.toggled.connect(self.onradioButtonProfileBlock)
        self.ui.radioButtonProfilePlan.toggled.connect(self.onradioButtonProfilePlan)

        self.logic.imageWidget = self.ui.label_profileDisplay # to display the profile

        # end code Olivier

        # Buttons
        self.ui.applyButton.connect("clicked(bool)", self.onApplyButton)

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

        # begin code Olivier 
        # Initial GUI update 
        #print("setup appel de updateGUIFromParameterNode()")       
        #self.updateGUIFromParameterNode()
        
        print("setup end")
        print("--------------------------")
        # end code Olivier

    def cleanup(self) -> None:
        """Called when the application closes and the module widget is destroyed."""
        print("cleanup begin")
        self.removeObservers()        
        print("cleanup end")

    def enter(self) -> None:
        """Called each time the user opens this module."""
        print("-----------------")
        print("enter begin")
        # Make sure parameter node exists and observed
        self.initializeParameterNode()
        print("enter end")
        print("-----------------")

    def exit(self) -> None:
        """Called each time the user opens a different module."""
        print("exit begin")
        # Do not react to parameter node changes (GUI will be updated when the user enters into the module)
        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self._parameterNodeGuiTag = None
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
        print("exit end")

    def onSceneStartClose(self, caller, event) -> None:
        """Called just before the scene is closed."""
        print("onSceneStartClose begin")
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)
        print("onSceneStartClose end")

    def onSceneEndClose(self, caller, event) -> None:
        """Called just after the scene is closed."""
        print("onSceneEndClose begin")
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()
        print("onSceneEndClose end")

    def initializeParameterNode(self) -> None:
        """Ensure parameter node exists and observed."""
        print("initializeParameterNode begin")
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())
       
        # Select default input nodes if nothing is selected yet to save a few clicks for the user
        if not self._parameterNode.inputVolume:
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")            
            if firstVolumeNode:
                self._parameterNode.inputVolume = firstVolumeNode
                # begin code Olivier
                self.logic.inputVolume = firstVolumeNode
                #print("initializeParameterNode self.logic.inputVolume = ", self.logic.inputVolume)
                # end code Olivier
        print("initializeParameterNode end")

    def setParameterNode(self, inputParameterNode: Optional[t_ZoomRoiParameterNode]) -> None:
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """
        print("setParameterNode begin")
        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            #self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply) # modif Olivier
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode) # modif Olivier
        self._parameterNode = inputParameterNode
        if self._parameterNode:
            # Note: in the .ui file, a Qt dynamic property called "SlicerParameterName" is set on each
            # ui element that needs connection.
            #print("self.ui.inputVolumeSelector = ", self.ui.inputVolumeSelector)
            print("setParameterNode self.ui.inputVolumeSelector = ", self.ui.inputVolumeSelector)            

            self._parameterNodeGuiTag = self._parameterNode.connectGui(self.ui)
            # self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply) # modif Olivier
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode) # modif Olivier
            self._checkCanApply() 
        # Initial GUI update # modif Olivier        
        self.updateGUIFromParameterNode()   # modif Olivier 
        print("setParameterNode end")   

    def _checkCanApply(self, caller=None, event=None) -> None:
        if self._parameterNode and self._parameterNode.inputVolume and self._parameterNode.thresholdedVolume:
            self.ui.applyButton.toolTip = _("Compute output volume")
            self.ui.applyButton.enabled = True
        else:
            self.ui.applyButton.toolTip = _("Select input and output volume nodes")
            self.ui.applyButton.enabled = False

    def onApplyButton(self) -> None:
        """Run processing when user clicks "Apply" button."""
        with slicer.util.tryWithErrorDisplay(_("Failed to compute results."), waitCursor=True):
            # Compute output
            self.logic.process(self.ui.inputVolumeSelector.currentNode(), self.ui.outputSelector.currentNode(),
                               self.ui.imageThresholdSliderWidget.value, self.ui.invertOutputCheckBox.checked)

            # Compute inverted output (if needed)
            if self.ui.invertedOutputSelector.currentNode():
                # If additional output volume is selected then result with inverted threshold is written there
                self.logic.process(self.ui.inputVolumeSelector.currentNode(), self.ui.invertedOutputSelector.currentNode(),
                                   self.ui.imageThresholdSliderWidget.value, not self.ui.invertOutputCheckBox.checked, showResult=False)

    # begin code Olivier
    def updateParameterNodeFromGUI(self, caller=None, event=None):
        """
      This method is called when the user makes any change in the GUI.
      The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
        """
        print("updateParameterNodeFromGUI begin")
        if self._parameterNode is None or self.logic is None or self._updatingGUIFromParameterNode:          
          return
      
        wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch
        settings=qt.QSettings(slicer.app.launcherSettingsFilePath, qt.QSettings.IniFormat)        
        self.pointX = self.ui.editPointX
        self.pointY = self.ui.editPointY
        self.pointZ = self.ui.editPointZ
        self.sizeX = self.ui.editSizeX
        self.sizeY = self.ui.editSizeY
        self.sizeZ = self.ui.editSizeZ
        self.radioButtonNoLink = self.ui.radioButtonNoLink.checked
        self.radioButtonSquare = self.ui.radioButtonSquare.checked
        self.radioButtonCube = self.ui.radioButtonCube.checked
        self.radioButtonfile = self.ui.radioButtonFile.checked
        print("updateParameterNodeFromGUI self.logic.fileDirectory = ", self.logic.fileDirectory)
        self.radioButtonDirectory = self.ui.radioButtonDirectory.checked
        self.logic.inputVolume = self.ui.inputVolumeSelector.currentNode()        
        if self.logic.inputVolume is None:
            print("updateParameterNodeFromGUI self.logic.inputVolume = None")
            return 
        if self.ui.inputVolumeSelector.currentNode() is None:
            print("updateParameterNodeFromGUI self.ui.inputVolumeSelector.currentNode() = None")
            return       
        #print("updateParameterNodeFromGUI self.ui.inputVolumeSelector.currentNode() = ", self.ui.inputVolumeSelector.currentNode())        
                
        if self.logic.inputVolumeBefore is not None:
            print("self.logic.inputVolume before = ", self.logic.inputVolumeBefore.GetName())
            saveName = self.logic.inputVolumeBefore.GetName()
            # save parameters
            self.saveDataToJson(saveName, self.logic.saveJsonDirectory)
            #self.logic.displayJsonData()
                
        print("self.logic.inputVolume after = ", self.logic.inputVolume.GetName() )
        self.logic.inputVolumeBefore = self.logic.inputVolume
        if self.ui.inputVolumeSelector.currentNode().GetStorageNode() is not None:
            self.logic.inputVolumeFileName = self.ui.inputVolumeSelector.currentNode().GetStorageNode().GetFileName()
              
        # load parameters        
        loadName = self.logic.inputVolume.GetName()
        self.loadDataFromJson(loadName, self.logic.saveJsonDirectory)
        self.pointX = self.ui.editPointX
        self.pointY = self.ui.editPointY
        self.pointZ = self.ui.editPointZ
        self.sizeX = self.ui.editSizeX
        self.sizeY = self.ui.editSizeY
        self.sizeZ = self.ui.editSizeZ
        self.radioButtonNoLink = self.ui.radioButtonNoLink.checked
        self.radioButtonSquare = self.ui.radioButtonSquare.checked
        self.radioButtonCube = self.ui.radioButtonCube.checked
        self.radioButtonFile = self.ui.radioButtonFile.checked
        self.radioButtonDirectory = self.ui.radioButtonDirectory.checked
        self.logic.zoom = self.ui.checkBoxZoom.checked
        if self.logic.zoom and self.logic.inputDirectory is not None:
            self.logic.saveJsonDirectoryZoom = self.logic.inputDirectory
            self.loadParamZoomFromJson(self.logic.inputDirectory, self.logic.saveJsonDirectoryZoom)        
        
        self.updateGUIFromParameterNode()
        # todo rajouter pour la zone de ROI


        self._parameterNode.EndModify(wasModified)
        print("updateParameterNodeFromGUI end")
        


    def updateGUIFromParameterNode(self, caller=None, event=None):
        """
      This method is called whenever parameter node is changed.
      The module GUI is updated to show the current state of the parameter node.
        """
        print("updateGUIFromParameterNode begin")        
        if self._parameterNode is None or self._updatingGUIFromParameterNode:          
          return
        # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
        self._updatingGUIFromParameterNode = True

        # Update node selectors and sliders
        self.ui.inputVolumeSelector.setCurrentNode(self.logic.inputVolume)
      
        # update slice views display
        #print("updateGUIFromParameterNode self.logic.inputVolume = ", self.logic.inputVolume)
        selectedVolumeNode = self.ui.inputVolumeSelector.currentNode()
        #print("updateGUIFromParameterNode selectedVolumeNode = ", selectedVolumeNode)
        #print("updateGUIFromParameterNode before sliceViewName = ")
        layoutManager = slicer.app.layoutManager()
        #for sliceViewName in layoutManager.sliceViewNames():
        #    compositeNode = layoutManager.sliceWidget(sliceViewName).sliceLogic().GetSliceCompositeNode()        
        #    volumeNodeID = compositeNode.GetBackgroundVolumeID()
        #    print(sliceViewName + ": " +volumeNodeID)
        #print("updateGUIFromParameterNode after sliceViewName = ")
        for sliceViewName in layoutManager.sliceViewNames():
            compositeNode = layoutManager.sliceWidget(sliceViewName).sliceLogic().GetSliceCompositeNode()
            if selectedVolumeNode is not None:
                compositeNode.SetBackgroundVolumeID(selectedVolumeNode.GetID())
            volumeNodeID = compositeNode.GetBackgroundVolumeID()
        #print(sliceViewName + ": " +volumeNodeID)
        slicer.app.applicationLogic().FitSliceToAll() # to center the slice
      
        # update the other ui
        if self.pointX  is not None:
            self.ui.editPointX = self.pointX 
        if self.pointY  is not None:
            self.ui.editPointY = self.pointY
        if self.pointZ  is not None:
            self.ui.editPointZ = self.pointZ
        if self.sizeX  is not None:
            self.ui.editSizeX = self.sizeX
        if self.sizeY  is not None:
            self.ui.editSizeY = self.sizeY
        if self.sizeZ  is not None:
            self.ui.editSizeZ = self.sizeZ
        if self.radioButtonNoLink  is not None:
            self.ui.radioButtonNoLink.checked =  self.radioButtonNoLink
        if self.radioButtonSquare  is not None:
            self.ui.radioButtonSquare.checked = self.radioButtonSquare
        if self.radioButtonCube  is not None:
            self.ui.radioButtonCube.checked = self.radioButtonCube
        if self.ui.checkBoxZoom is not None:
            self.ui.checkBoxZoom.checked = self.logic.zoom            
        if self.radioButtonFile  is not None:
            self.ui.radioButtonFile.checked = self.radioButtonFile
            if self.logic.inputVolumeFileName is not None:
                self.logic.retrieveSizeImageNrrd()
                self.majFileInfo()
        if self.radioButtonDirectory  is not None:
            self.ui.radioButtonDirectory.checked = self.radioButtonDirectory
        
        if not self.logic.zoom:            
            self.eraseAreaZoom()
        else:
            self.drawAreaZoom()
      
        # All the GUI updates are done
        self._updatingGUIFromParameterNode = False
        print("updateGUIFromParameterNode end")


    def onCreateROIButton(self):
        """
        Handler for the Create ROI button click event.

        This function is triggered when the "Create ROI" button is clicked. It performs 
        a series of checks to ensure that all necessary inputs and configurations are valid 
        before calling the `createRoi` method from the logic with the center and size of the ROI to create a Region of Interest (ROI).    

        Returns:
        None
        """
        print("Button Create ROI clicked")
        if not self.logic.inputVolume: 
            slicer.util.warningDisplay("Please load and select an input volume!\n")
            return
        if not self.logic.inputDirectory: 
            slicer.util.warningDisplay("Please select an input directory!\n")
            return
        if not self.logic.outputFile: 
            slicer.util.warningDisplay("Please select an output file!\n")
            return
        if not self.logic.createdRoi:
            slicer.util.warningDisplay("Please create a ROI!\n")
            return
        if not self.logic.programDirectory:
            slicer.util.warningDisplay("Please select a program directory!\n")
            return       
                
        centerRoi = []
        centerRoi.append(self.logic.centerROI[0])
        centerRoi.append(self.logic.centerROI[1])
        centerRoi.append(self.logic.centerROI[2])
        sizeRoi = []
        sizeRoi.append(self.logic.sizeROI[0])
        sizeRoi.append(self.logic.sizeROI[1])
        sizeRoi.append(self.logic.sizeROI[2])
        print("onCreateROIButton centerRoi = ", centerRoi)
        print("onCreateROIButton sizeRoi = ", sizeRoi)      
        self.logic.createRoi(centerRoi, sizeRoi)        
       

    def onPointModifiedEvent(self, caller, eventId):
        """
        Event handler for point modification events.

        This function is called when a point representing a Region of Interest (ROI) 
        is modified. It updates the center and size of the ROI based on the modifications 
        and reflects these changes in the user interface. Additionally, it adjusts the 
        slice offsets in the 3D visualization to focus on the modified ROI.

        Parameters:
        caller: The object that triggered the event, typically representing the modified point.        

        Returns:
        None
        """
        print("onPointModifiedEvent")            
        self.logic.centerROI = caller.GetCenter()
        self.logic.createdRoi = True        
        self.logic.centerROI[0], self.logic.centerROI[1], self.logic.centerROI[2] = self.convertRasToIjk(self.logic.centerROI[0], self.logic.centerROI[1], self.logic.centerROI[2]) 
        if self.logic.centerROI == (-1,-1,-1) or self.logic.factorResize is None:
            return 
        self.logic.sizeROITuple = caller.GetSize()
        self.logic.sizeROI = list(self.logic.sizeROITuple)        
        self.ui.editPointX.setText(str(round(self.logic.centerROI[0] * self.logic.factorResize)))
        self.ui.editPointY.setText(str(round(self.logic.centerROI[1] * self.logic.factorResize)))
        self.ui.editPointZ.setText(str(round(self.logic.centerROI[2] * self.logic.factorResize)))
        self.ui.editSizeX.setText(str(round(self.logic.sizeROI[0] * self.logic.factorResize)))
        self.ui.editSizeY.setText(str(round(self.logic.sizeROI[1] * self.logic.factorResize)))
        self.ui.editSizeZ.setText(str(round(self.logic.sizeROI[2] * self.logic.factorResize)))
        self.changeSliceOffset(2, "Red", self.logic.centerROI[2])
        self.changeSliceOffset(1, "Green", self.logic.centerROI[1]) 
        self.changeSliceOffset(0, "Yellow", self.logic.centerROI[0])
        self.logic.createdRoi = True
        
    def onProfilePointModifiedEventOrigin(self, caller, eventId):
        """
        Event handler for modifications to the origin point of a profile.

        This function is called when the origin point of a profile is modified. It retrieves 
        the new center position from the caller and passes it to another event handler for 
        further processing.

        Parameters:
        caller: The object that triggered the event, typically representing the modified profile point.        

        Returns:
        None
        """
        print("onProfilePointModifiedEventOrigin")
        centerProfile = caller.GetCenter() 
        self.onProfilePointModifiedEvent(centerProfile, 0, self.logic.fileDirectory)


    def onProfilePointModifiedEventDestination(self, caller, eventId):
        """
        Event handler for modifications to the destination point of a profile.

        This function is called when the destination point of a profile is modified. It retrieves 
        the new center position from the caller and passes it to another event handler for 
        further processing.

        Parameters:
        caller: The object that triggered the event, typically representing the modified profile point.    

        Returns:
        None
        """
        print("onProfilePointModifiedEventDestination")
        centerProfile = caller.GetCenter() 
        self.onProfilePointModifiedEvent(centerProfile, 1, self.logic.fileDirectory)

    
    def onProfilePointModifiedEvent(self, centerProfile, originDestination, fileDirectory):
        """
        Event handler for modifications to a profile point's coordinates.

        This function is called when the coordinates of a profile point are modified. It converts 
        the coordinates from RAS (Right-Anterior-Superior) to IJK (Image Index) format and updates 
        the UI elements corresponding to the profile's origin or destination point based on the 
        provided parameters and adjust the slice offsets in the visualization according to the new coordinates.

        Parameters:
        centerProfile (tuple): A tuple containing the RAS coordinates of the profile point (x, y, z).
        originDestination (int): An identifier that indicates whether the point is an origin (0) 
                                or a destination (1).
        fileDirectory (str): A string indicating the context of the operation, used to determine 
                            the resizing factor.

        Returns:
        None
        """
        print("onProfilePointModifiedEvent")              
        coord = self.convertRasToIjk(centerProfile[0], centerProfile[1], centerProfile[2])        
        print("onProfilePointModifiedEvent coord = ", coord) 
        if coord == (-1,-1,-1) or self.logic.factorResize is None:
            return 
        factorResize =  self.logic.factorResize
        if fileDirectory == "f":
            factorResize = 1
        print("onMouseMoved factorResize = ", factorResize)
        if originDestination == 0:
            self.ui.editProfileX.setText(str(coord[0]*factorResize))
            self.ui.editProfileY.setText(str(coord[1]*factorResize))
            self.ui.editProfileZ.setText(str(coord[2]*factorResize))
        else:
            self.ui.editProfileXDestination.setText(str(coord[0]*factorResize))
            self.ui.editProfileYDestination.setText(str(coord[1]*factorResize))
            self.ui.editProfileZDestination.setText(str(coord[2]*factorResize))    
        self.changeSliceOffset(2, "Red", coord[2])
        self.changeSliceOffset(1, "Green", coord[1]) 
        self.changeSliceOffset(0, "Yellow", coord[0])    

    def onInputFilePathLineEditChanged(self):
        """
        Event handler for changes in the input file path line edit.

        This function is triggered when the user modifies the input file path in the line edit widget.
        It updates the logic layer's `inputFile` attribute with the new path provided by the user.    

        Returns:
        None
        """
        print("onInputFilePathLineEditChanged")
        self.logic.inputFile = self.ui.inputFilePathLineEdit.currentPath
        print("onInputFilePathLineEditChanged self.logic.inputFile = ", self.logic.inputFile)

    
    def onInputDirectoryPathLineEditChanged(self):
        """"
        Event handler for changes in the input directory path line edit.

        This function is triggered when the user modifies the input directory path in the line edit widget.
        It updates the logic layer's `inputDirectory` attribute with the new path provided by the user and
        performs various operations to ensure that the application is set up correctly with the new directory.   

        Returns:
        None
        """
        print("onInputDirectoryPathLineEditChanged")
        self.logic.inputDirectory = self.ui.inputDirectoryPathLineEdit.currentPath
        print("self.logic.inputDirectory = ", self.logic.inputDirectory)
        # TODO voir ce qui passe si le dossier choisi n'est pas un bon dossier contenant les images jp2        
        print("onInputDirectoryPathLineEditChanged self.ui.inputVolumeSelector.currentNode() = ", self.ui.inputVolumeSelector.currentNode())        
        self.logic.retrieveSizeImage()
        self.updateMaxSlider()
        if self.ui.inputVolumeSelector.currentNode() is not None and self.ui.inputVolumeSelector.currentNode().GetStorageNode() is not None:
            self.logic.computeFactorResize()
        self.ui.radioButtonDirectory.setChecked(True)
        self.logic.fileDirectory == "d"
        self.radioButtonDirectory = True        
        self.radioButtonFile = False
        
    def onProgramDirectoryPathLineEditChanged(self):
        """"
        Event handler for changes in the program directory path line edit.

        This function is called when the user modifies the program directory path in the line edit widget.
        It updates the logic layer's `programDirectory` attribute with the new path provided by the user 
        and saves the configuration to ensure that the new directory is preserved for future sessions.   

        Returns:
        None
        """
        print("onProgramDirectoryPathLineEditChanged")
        self.logic.programDirectory = self.ui.programDirectoryPathLineEdit.currentPath
        print("self.logic.programDirectory = ", self.logic.programDirectory)
        self.logic.saveConfiguration()

    
    def updateMaxSlider(self):
        """
        Updates the maximum value of the slice range slider based on the size of the input image.

        This function calculates the maximum value for the slice range slider by subtracting one from the 
        `sizeZImageInputOrigin`, which represents the total number of slices in the input volume. 
        It then updates the `maximum` and `maximumValue` properties of the `RangeWidgetSlices` UI component 
        to reflect this new maximum value.   

        Returns:
        None
        """
        print("updateMaxSlider")
        self.maxSlider = self.logic.sizeZImageInputOrigin-1        
        self.ui.RangeWidgetSlices.maximum = self.maxSlider       
        self.ui.RangeWidgetSlices.maximumValue = self.maxSlider
        

    def onOutputFilePathLineEditChanged(self):
        """"
        Handles changes in the output file path line edit.

        This function is triggered when the user modifies the output file path in the corresponding UI element. 
        It updates the `outputFile` attribute of the `logic` object with the new file path provided by the user 
        through the UI.

        Returns:
        None
        """
        print("onOutputFilePathLineEditChanged")
        self.logic.outputFile = self.ui.outputFilePathLineEdit.currentPath
        print("self.logic.outputFile= ", self.logic.outputFile)

    def onResizedOutputFilePathLineEditChanged(self):
        """"
        Handles changes in the resized output file path line edit.

        This function is triggered when the user modifies the output file path for the resized image 
        in the corresponding UI element. It updates the `outputFileResized` attribute of the `logic` 
        object with the new file path provided by the user.    

        Returns:
        None
        """
        print("onResizedOutputFilePathLineEditChanged")
        self.logic.outputFileResized = self.ui.PathLineEditOutputfileResized.currentPath
        print("self.logic.outputFileResized= ", self.logic.outputFileResized)

    def onProfileOutputFilePathLineEditChanged(self):
        """
        Handles changes in the profile output file path line edit.

        This function is triggered when the user modifies the output file path for the profile data 
        in the corresponding UI element. It updates the `profileOutputFile` attribute of the `logic` 
        object with the new file path provided by the user.    

        Returns:
        None
        """
        print("onProfileOutputFilePathLineEditChanged")
        self.logic.profileOutputFile = self.ui.profileOutputFilePathLineEdit.currentPath
        print("self.logic.profileOutputFile= ", self.logic.profileOutputFile)

    def onProfileFilePathLineEditChanged(self):
        """"
        Handles changes in the profile file path line edit.

        This function is triggered when the user modifies the input file path for the profile data
        in the corresponding UI element. It updates the `profileFile` attribute of the `logic` 
        object with the new file path provided by the user.    

        Returns:
        None
        """
        print("onProfileFilePathLineEditChanged")
        self.logic.profileFile = self.ui.profileFilePathLineEdit.currentPath
        print("self.logic.profileFile= ", self.logic.profileFile)

    def onRangeWidgetSlicesChanged(self):
        """
        Handles changes in the range widget for slice selection.

        This function is triggered when the user modifies the range of slices using the range widget
        in the UI. It updates the `beginSlice` and `endSlice` attributes of the `logic` object 
        to reflect the new selected slice range.    

        Returns:
        None
        """
        print("onRangeWidgetSlicesChanged")
        print("onRangeWidgetSlicesChanged self.ui.RangeWidgetSlices.maximumValue = ", self.ui.RangeWidgetSlices.maximumValue)
        self.logic.endSlice  = self.ui.RangeWidgetSlices.maximumValue
        self.logic.beginSlice = self.ui.RangeWidgetSlices.minimumValue
        self.majOutputResizedInfo()

    def onSliderWidgetFactorResizeChanged(self):
        """"
        Handles changes in the slider widget for resizing factor.

        This function is triggered when the user adjusts the value of the slider widget
        that controls the factor for resizing images. It updates the `sliderFactorResizeValue`
        attribute of the `logic` object with the new value from the slider.

        Returns:
        None
        """
        print("onSliderWidgetFactorResizeChanged")
        self.logic.sliderFactorResizeValue = self.ui.SliderWidgetFactorResize.value
        self.majOutputResizedInfo()

    def onSliderWidgetNeighborChanged(self):
        """"
        Handles changes in the slider widget for neighbor selection.

        This function is triggered when the user adjusts the value of the slider widget 
        that controls the number of neighbors considered in the application's operations. 
        It updates the `sliderNeighbor` attribute of the `logic` object with the new 
        value from the slider.    
    
        Returns:
        None
        """
        print("onSliderWidgetNeighborChanged")        
        self.logic.sliderNeighbor = self.ui.SliderWidgetNeighbor.value
        print("onSliderWidgetNeighborChanged self.logic.sliderNeighbor = ", self.logic.sliderNeighbor)

    def onSliderWidgetStepChanged(self):
        """"
         Handles changes in the slider widget for step size selection.

        This function is triggered when the user adjusts the value of the slider widget 
        that controls the step size used in the application's operations. 
        It updates the `sliderStep` attribute of the `logic` object with the new 
        value from the slider.    
    
        Returns:
        None
        """
        print("onSliderWidgetStepChanged")        
        self.logic.sliderStep = self.ui.SliderWidgetSteps.value
        print("onSliderWidgetStepChanged self.logic.sliderStep = ", self.logic.sliderStep)


    def editPointXChanged(self):
        """
        Handles changes in the X coordinate input field for the ROI center.

        This function is triggered when the user modifies the value of the input field 
        corresponding to the X coordinate of the center of the Region of Interest (ROI). 
        It updates the center of the ROI based on the new X value provided by the user.
    
        Returns:
        None
        """
        print("editPointXChanged")          
        self.editCenterChanged(self.ui.editPointX,0)
        self.pointX = self.ui.editPointX
            


    def editPointYChanged(self):
        """
        Handles changes in the Y coordinate input field for the ROI center.

        This function is triggered when the user modifies the value of the input field 
        corresponding to the Y coordinate of the center of the Region of Interest (ROI). 
        It updates the center of the ROI based on the new Y value provided by the user.
    
        Returns:
        None
        """
        print("editPointYChanged")
        self.editCenterChanged(self.ui.editPointY,1)
        self.pointY = self.ui.editPointY
        

    def editPointZChanged(self):
        """
        Handles changes in the Z coordinate input field for the ROI center.

        This function is triggered when the user modifies the value of the input field 
        corresponding to the Z coordinate of the center of the Region of Interest (ROI). 
        It updates the center of the ROI based on the new Z value provided by the user.
    
        Returns:
        None
        """
        print("editPointZChanged")
        self.editCenterChanged(self.ui.editPointZ,2)
        self.pointZ = self.ui.editPointZ

    def editCenterChanged(self, centerUi, position):
        """"
        Updates the center of the Region of Interest (ROI) based on user input.

        This method is triggered when the user changes the value of a coordinate input field
        for the ROI center. It modifies the corresponding coordinate of the ROI's center in the 
        markups node based on the user input, converting it from IJK to RAS coordinates.

        Parameters:
        - centerUi: The UI element representing the coordinate input (QLineEdit).
        - position: An integer indicating which coordinate is being modified:
            - 0: X coordinate
            - 1: Y coordinate
            - 2: Z coordinate    

        Returns:
        None
        """
        print("editCenterChanged")
        if centerUi.text == "":
            return
        if  int(centerUi.text) <0:
            centerUi.setText("0")              
        centerRoi = self.markupsNode.GetCenter()       
        
        # convert IJK to RAS
        newCenter = int(centerUi.text)/self.logic.factorResize
        # to do compute the matrix

        if position == 0:
            self.markupsNode.SetCenter(newCenter, centerRoi[1], centerRoi[2])
        elif position == 1:
            self.markupsNode.SetCenter(centerRoi[0], newCenter, centerRoi[2])
        else:
            self.markupsNode.SetCenter(centerRoi[0], centerRoi[1], newCenter)                     
        #print("centeROI after = ", self.markupsNode.GetCenter())
        #print("editCenterChanged self.ui.editPointX.text = ", self.ui.editPointX.text)  

    
    def editSizeXChanged(self):
        """"
        Handles the change event for the X size input field of the Region of Interest (ROI).

        This method is triggered when the user modifies the X size of the ROI. It updates the 
        corresponding size in the markups node and adjusts the sizes of Y and Z dimensions 
        if certain conditions are met.    

        Returns:
        None
        """
        #print("sizeX max", self.logic.sizeImageInputOrigin[0])        
        self.editSizeChanged(self.ui.editSizeX, 0)
        if self.logic.shape != "n":
            self.changeSize(self.ui.editSizeY, 1, self.ui.editSizeX.text)
        if self.logic.shape == "c":
            self.changeSize(self.ui.editSizeZ, 2, self.ui.editSizeX.text)        
        self.sizeX = self.ui.editSizeX     

    def editSizeYChanged(self):
        """"
        Handles the change event for the Y size input field of the Region of Interest (ROI).

        This method is triggered when the user modifies the Y size of the ROI. It updates the 
        corresponding size in the markups node and adjusts the sizes of X and Z dimensions 
        if certain conditions are met.    

        Returns:
        None
        """
        #print("sizeY max", self.logic.sizeImageInputOrigin[1])        
        self.editSizeChanged(self.ui.editSizeY, 1)
        if self.logic.shape != "n":
            self.changeSize(self.ui.editSizeX, 0, self.ui.editSizeY.text)
        if self.logic.shape == "c":
            self.changeSize(self.ui.editSizeZ, 2, self.ui.editSizeY.text)
        self.sizeY = self.ui.editSizeY


    def editSizeZChanged(self):        
        """"
        Handles the change event for the ZE size input field of the Region of Interest (ROI).

        This method is triggered when the user modifies the Z size of the ROI. It updates the 
        corresponding size in the markups node and adjusts the sizes of X and Y dimensions 
        if certain conditions are met.    

        Returns:
        None
        """
        self.editSizeChanged(self.ui.editSizeZ, 2)
        if self.logic.shape == "c":
            self.changeSize(self.ui.editSizeX, 0, self.ui.editSizeZ.text)
            self.changeSize(self.ui.editSizeY, 1, self.ui.editSizeZ.text)
        self.sizeZ = self.ui.editSizeZ     
        

    def editSizeChanged(self, sizeUi, position):
        """
        Updates the size of the Region of Interest (ROI) based on user input.

        This method is triggered when the user modifies the size of a dimension (X, Y, or Z) 
        in the ROI. It validates the input and ensures that the size does not exceed the 
        maximum allowable values. The updated size is then applied to the ROI.

        Parameters:
        - sizeUi: The user interface element (e.g., QLineEdit) containing the size input.
        - position: An integer representing the dimension being modified:
            - 0: X dimension
            - 1: Y dimension
            - 2: Z dimension    

        Returns:
        None
        """
        print("editSizeChanged")
        if sizeUi.text == "":
            return
        if  int(sizeUi.text) <0:
            sizeUi.setText("0")
        if position !=2 and int(sizeUi.text) > self.logic.sizeImageInputOrigin[position]:
            sizeUi.setText(str(self.logic.sizeImageInputOrigin[position]))
        if position ==2 and int(sizeUi.text) > self.logic.sizeZImageInputOrigin:
            sizeUi.setText(str(self.logic.sizeZImageInputOrigin))
        sizeNew = int(sizeUi.text)             
        sizeRoi = self.markupsNode.GetSize()        
        if position == 0:
            self.markupsNode.SetSize(sizeNew/self.logic.factorResize, sizeRoi[1], sizeRoi[2])
        elif position == 1:
            self.markupsNode.SetSize(sizeRoi[0],sizeNew/self.logic.factorResize, sizeRoi[2])
        else:
            self.markupsNode.SetSize(sizeRoi[0], sizeRoi[1], sizeNew/self.logic.factorResize)                     
        
        
    def changeSize(self, sizeUi, position, value):
        """
        Updates the size of a specific dimension in the Region of Interest (ROI) 
        by setting the provided value in the user interface element and invoking
        the size change handling logic.

        This method is designed to facilitate the modification of the size of 
        the ROI by programmatically changing the value in the associated UI 
        component and ensuring that the corresponding size change logic is executed.

        Parameters:
        - sizeUi: The user interface element (e.g., QLineEdit) that displays 
        the size for a specific dimension (X, Y, or Z).
        - position: An integer indicating which dimension's size is being modified:
            - 0: X dimension
            - 1: Y dimension
            - 2: Z dimension
        - value: The new size value to set in the user interface for the specified dimension.

        Returns:
        None
        """
        sizeUi.setText(value)
        self.editSizeChanged(sizeUi, position)
    
    def onradioButtonNoLink(self):
        """"
         Handles the event when the 'No Links' radio button is selected.

        This function is triggered when the user clicks on the 'No Links' radio button 
        in the user interface. It sets  `self.logic.shape` to "n" (indicating 'no links').    

        Returns:
        None
        """
        print("No links clicked")
        self.logic.shape = "n"

    def onradioButtonSquare(self):
        """"
         Handles the event when the 'Square clicked' radio button is selected.

        This function is triggered when the user clicks on the 'Square' radio button 
        in the user interface. It sets  `self.logic.shape` to "s" (indicating 'Square').    

        Returns:
        None
        """
        print("Square clicked")
        self.logic.shape = "s"
    
    def onradioButtonCube(self):
        """"
         Handles the event when the 'Cube clicked' radio button is selected.

        This function is triggered when the user clicks on the 'Cube' radio button 
        in the user interface. It sets  `self.logic.shape` to "c" (indicating 'Cube').    

        Returns:
        None
        """
        print("Cube clicked")
        self.logic.shape = "c"
    
    def changeSliceOffset(self, pos, sliceWidgetColor, newPos):
        """"
        Changes the slice offset for a specified slice widget in the Slicer application.

        This function updates the position of a slice widget (e.g., axial, sagittal, coronal)
        in the Slicer layout. It allows for the visualization of different slices of the loaded 
        volume based on the provided position and color of the slice widget.

        Parameters:
        - pos (int): The position identifier for the slice widget. 
                    Not explicitly used in the function but could be part of a larger 
                    interface.
        - sliceWidgetColor (str): The color of the slice widget to update. 
                                Common values include "Red", "Green", and "Yellow" 
                                corresponding to the different views in Slicer.
        - newPos (int): The new offset value for the slice widget. This value is adjusted 
                        for the Green slice widget, as its direction is inverted.
   
        Returns:
        None
        """
        print("changeSliceOffset")
        layoutManager = slicer.app.layoutManager()
        colorSlice = layoutManager.sliceWidget(sliceWidgetColor).sliceLogic()               
        if sliceWidgetColor == "Green":
            newPos = -newPos 
        colorSlice.SetSliceOffset(newPos)
        #print("newPos = ", colorSlice.GetSliceOffset()) 

    def saveDataToJson(self, saveName, directory):
        """"
        Saves the current configuration and parameters of the application to a JSON file.

        This method collects various parameters and states from the application's user interface
        and logic layer, constructs a dictionary, and serializes it to a JSON file. If the specified 
        directory does not exist, it creates it. The JSON file is named using the provided saveName.

        Parameters:
        - saveName (str): The name to be used for the JSON file (without extension).
        - directory (str): The directory path where the JSON file will be saved.    

        Returns:
        None
        """
        print("saveDataToJson")        
        if not os.path.exists(directory):
            os.makedirs(directory)
        self.logic.dictionary = {}
        self.logic.dictionary["Name"] = saveName
        self.logic.dictionary["editPointX"] = ""
        self.logic.dictionary["editPointY"] = ""
        self.logic.dictionary["editPointZ"] = ""
        self.logic.dictionary["editSizeX"] = ""
        self.logic.dictionary["editSizeY"] = ""
        self.logic.dictionary["editSizeZ"] = ""
        self.logic.dictionary["inputDirectory"] = ""
        self.logic.dictionary["outputFile"] = ""
        self.logic.dictionary["roiCreated"] = ""
        self.logic.dictionary["beginSlice"] = ""
        self.logic.dictionary["endSlice"] = ""
        self.logic.dictionary["outputFileResized"] = ""
        self.logic.dictionary["sliderFactorResize"] = "1"
        self.logic.dictionary["zoomEnabled"] = "False"
        self.logic.dictionary["isFile"] = "False"
        self.logic.dictionary["editProfileX"] = ""
        self.logic.dictionary["editProfileY"] = ""
        self.logic.dictionary["editProfileZ"] = ""
        self.logic.dictionary["editProfileXDestination"] = ""
        self.logic.dictionary["editProfileYDestination"] = ""
        self.logic.dictionary["editProfileZDestination"] = ""
        self.logic.dictionary["profileVector"] = ""
        self.logic.dictionary["neighborDistance"] = ""
        self.logic.dictionary["numberOfPoints"] = ""
        self.logic.dictionary["profileFileDirectory"] = ""
        self.logic.dictionary["profileOutputFile"] = ""
        self.logic.dictionary["profileFile"] = ""

        if self.ui.editPointX is not None:
            self.logic.dictionary["editPointX"] = self.ui.editPointX.text
        if self.ui.editPointY is not None:
            self.logic.dictionary["editPointY"] = self.ui.editPointY.text
        if self.ui.editPointZ is not None:
            self.logic.dictionary["editPointZ"] = self.ui.editPointZ.text
        if self.ui.editSizeX is not None:
            self.logic.dictionary["editSizeX"] = self.ui.editSizeX.text
        if self.ui.editSizeY is not None:
            self.logic.dictionary["editSizeY"] = self.ui.editSizeY.text
        if self.ui.editSizeZ is not None:
            self.logic.dictionary["editSizeZ"] = self.ui.editSizeZ.text
        if self.logic.inputDirectory is not None:
            self.logic.dictionary["inputDirectory"] = self.logic.inputDirectory
            print("saveDataToJson self.logic.inputDirectory = ", self.logic.inputDirectory)
        if self.logic.outputFile is not None:
            self.logic.dictionary["outputFile"] = self.logic.outputFile
        if self.logic.createdRoi:
            self.logic.dictionary["roiCreated"] = "true"
        if self.logic.inputDirectory is not None and self.logic.beginSlice is not  None:
            self.logic.dictionary["beginSlice"] = self.logic.beginSlice
            print("saveDataToJson self.logic.beginSlice = ", self.logic.beginSlice)
        if self.logic.inputDirectory is not None and self.logic.endSlice is not  None:
            self.logic.dictionary["endSlice"] = self.logic.endSlice
            print("saveDataToJson self.logic.endSlice = ", self.logic.endSlice)
        if self.logic.outputFileResized is not None:
            self.logic.dictionary["outputFileResized"] = self.logic.outputFileResized
        if self.logic.sliderFactorResizeValue is not None:
            self.logic.dictionary["sliderFactorResize"] = self.logic.sliderFactorResizeValue
        if self.logic.zoom:
            self.logic.dictionary["zoomEnabled"] = "True"
        if self.logic.dictionary["inputDirectory"] == "":
            self.logic.dictionary["isFile"] = "True"
        if self.ui.editProfileX is not None:
            self.logic.dictionary["editProfileX"] = self.ui.editProfileX.text
        if self.ui.editProfileY is not None:
            self.logic.dictionary["editProfileY"] = self.ui.editProfileY.text
        if self.ui.editProfileZ is not None:
            self.logic.dictionary["editProfileZ"] = self.ui.editProfileZ.text
        if self.ui.editProfileXDestination is not None:
            self.logic.dictionary["editProfileXDestination"] = self.ui.editProfileXDestination.text
        if self.ui.editProfileYDestination is not None:
            self.logic.dictionary["editProfileYDestination"] = self.ui.editProfileYDestination.text
        if self.ui.editProfileZDestination is not None:
            self.logic.dictionary["editProfileZDestination"] = self.ui.editProfileZDestination.text
        if self.logic.profileNormalDirection is not None:
            self.logic.dictionary["profileVector"] = self.logic.profileNormalDirection
        if self.logic.sliderNeighbor is not None:
            self.logic.dictionary["neighborDistance"] = self.logic.sliderNeighbor
        if self.logic.sliderStep is not None:
            self.logic.dictionary["numberOfPoints"] = self.logic.sliderStep
        if self.logic.profileFileDirectory is not None:
            self.logic.dictionary["profileFileDirectory"] = self.logic.profileFileDirectory
        if self.logic.profileOutputFile is not None:
            self.logic.dictionary["profileOutputFile"] = self.logic.profileOutputFile
        if self.logic.profileFile is not None:
            self.logic.dictionary["profileFile"] = self.logic.profileFile   
        
        json_object = json.dumps(self.logic.dictionary, indent=4)
        print("saveDataToJson outfile = ", directory + saveName + ".json")
        with open(directory + saveName + ".json", "w") as outfile:
            outfile.write(json_object)

    
    def loadDataFromJson(self, loadName, directory):
        """"
        Loads configuration and parameters from a JSON file into the application's UI and logic.

        This method reads a JSON file specified by the provided loadName and directory, and populates
        various user interface elements and internal logic variables with the values retrieved from the file. 
        It validates the existence of the specified directory and file before attempting to load the data.

        Parameters:
        - loadName (str): The name of the JSON file to be loaded (without extension).
        - directory (str): The directory path where the JSON file is located.    

        Returns:
        None
        """
        print("loadDataFromJson")
        if not os.path.exists(directory):
            print(directory + " does not exist!") 
            self.resetEditLine()
            return
        if not os.path.isfile(directory + loadName + ".json"):
            print(directory + loadName + ".json" + " does not exist!")
            self.resetEditLine() 
            return
        with open(directory + loadName + ".json", "r") as openfile:
            param = json.load(openfile)        
        print("param = ", param)
        self.ui.editPointX.setText(param["editPointX"])
        self.ui.editPointY.setText(param["editPointY"])
        self.ui.editPointZ.setText(param["editPointZ"])
        self.ui.editSizeX.setText(param["editSizeX"])
        self.ui.editSizeY.setText(param["editSizeY"])
        self.ui.editSizeZ.setText(param["editSizeZ"])
        self.ui.inputDirectoryPathLineEdit.setCurrentPath(param["inputDirectory"])
        self.logic.inputDirectory = param["inputDirectory"]        
        self.ui.outputFilePathLineEdit.setCurrentPath(param["outputFile"])
        self.logic.outputFile = param["outputFile"]
        if param["zoomEnabled"] == "False":
            self.ui.checkBoxZoom.checked = False
        else:
            self.ui.checkBoxZoom.checked = True
        if param["roiCreated"] == "true":
            print("")
            #self.changeSliceOffset(2, "Red")
            #self.changeSliceOffset(1, "Green") 
            #self.changeSliceOffset(0, "Yellow")
            #self.logic.createdRoi = True
        if param["beginSlice"] != "":
            self.ui.RangeWidgetSlices.minimumValue = float(param["beginSlice"])
        else:
            self.ui.RangeWidgetSlices.minimumValue = 0.0
        if param["endSlice"] != "":
            self.ui.RangeWidgetSlices.maximumValue = float(param["endSlice"])
        else:
            self.ui.RangeWidgetSlices.maximum = 0.0
            self.ui.RangeWidgetSlices.maximumValue = 0.0
        self.ui.PathLineEditOutputfileResized.setCurrentPath(param["outputFileResized"])
        self.logic.outputFileResized = param["outputFileResized"]
        if param["sliderFactorResize"] != "":
            self.ui.SliderWidgetFactorResize.value = float(param["sliderFactorResize"])
        else:
            self.ui.SliderWidgetFactorResize.value = 1.0
        if param["isFile"] == "True":           
            self.ui.radioButtonFile.setChecked(True)
            self.logic.fileDirectory == "f"
            self.radioButtonFile = True
            self.radioButtonDirectory = False         
        else:            
            self.ui.radioButtonDirectory.setChecked(True)
            self.logic.fileDirectory == "d"
            self.radioButtonDirectory = True
            self.radioButtonFile = False
        self.ui.editProfileX.setText(param["editProfileX"])
        self.ui.editProfileY.setText(param["editProfileY"])
        self.ui.editProfileZ.setText(param["editProfileZ"])
        self.ui.editProfileXDestination.setText(param["editProfileXDestination"])
        self.ui.editProfileYDestination.setText(param["editProfileYDestination"])
        self.ui.editProfileZDestination.setText(param["editProfileZDestination"])
        self.ui.SliderWidgetNeighbor.value = float(param["neighborDistance"])
        self.logic.sliderNeighbor = float(param["neighborDistance"])
        self.ui.SliderWidgetSteps.value = float(param["numberOfPoints"])
        self.logic.sliderStep = float(param["numberOfPoints"])
        self.ui.profileOutputFilePathLineEdit.setCurrentPath(param["profileOutputFile"])
        self.logic.profileOutputFile = param["profileOutputFile"]
        self.ui.profileFilePathLineEdit.setCurrentPath(param["profileFile"])
        self.logic.profileFile = param["profileFile"]
        if param["profileVector"] == "n":
            self.ui.radioButtonProfileNormal.setChecked(True)
            self.logic.profileNormalDirection = "n"
        else: 
            self.ui.radioButtonProfileDirection.setChecked(True)
            self.logic.profileNormalDirection = "d"
        if param["profileFileDirectory"] == "f":            
            self.logic.profileFileDirectory = "f"        
        

    def loadParamZoomFromJson(self, loadName, directory):
        """"
        Loads zoom parameters from a JSON file into the application's logic.

        This method attempts to read zoom configuration data from a specified JSON file
        and updates the internal logic state to reflect the loaded zoom parameters.
        It verifies the existence of the specified directory and file before attempting to load the data.

        Parameters:
        - loadName (str): The name of the JSON file containing zoom parameters (without extension).
        - directory (str): The directory path where the JSON file is located.
    
        Returns:
        None
        """
        print("loadParamZoomFromJson")
        self.logic.zoomJsonExist = False
        self.logic.zoom = False        
        if not os.path.exists(directory):
            print(directory + " does not exist!")            
            return
        head_tail = os.path.split(loadName)
        print("head_tail[0]", head_tail[0])
        print("head_tail[1]", head_tail[1])
        if not os.path.isfile(directory  + "/" + head_tail[1] + ".json"):
            print(directory + "/" + head_tail[1] + ".json" + " does not exist!")
            slicer.util.warningDisplay("Zoom areas are not defined!\n")
            return
        with open(directory + "/" + head_tail[1] + ".json", "r") as openfile:
            self.logic.paramZoom = json.load(openfile)
            self.logic.zoomJsonExist = True
            self.logic.zoom = True        
        print("loadParamZoomFromJson param = ", self.logic.paramZoom)    


    def resetEditLine(self):
        """"
        Resets all input fields and UI components to their default state.

        This method clears all text input fields, resets the slider values, 
        and clears the current paths for the directory and output files. 
        It also updates the logic variables associated with the input parameters to ensure
        the application starts from a clean state.

        Returns:
        None
        """
        print("resetEditLine")
        self.ui.editPointX.setText("")
        self.ui.editPointY.setText("")
        self.ui.editPointZ.setText("")
        self.ui.editSizeX.setText("")
        self.ui.editSizeY.setText("")
        self.ui.editSizeZ.setText("")
        self.ui.inputDirectoryPathLineEdit.setCurrentPath("")
        self.logic.inputDirectory = None
        self.ui.outputFilePathLineEdit.setCurrentPath("")        
        self.logic.beginSlice = None
        self.logic.endSlice = None        
        self.ui.checkBoxZoom.checked = False
        self.ui.RangeWidgetSlices.maximum = 1.0
        self.ui.RangeWidgetSlices.minimumValue = 0.0
        self.ui.RangeWidgetSlices.maximumValue = 1.0
        print("resetEditLine self.ui.RangeWidgetSlices.maximumValue = ", self.ui.RangeWidgetSlices.maximumValue)
        self.ui.editProfileX.setText("")
        self.ui.editProfileY.setText("")
        self.ui.editProfileZ.setText("")
        self.ui.editProfileXDestination.setText("")
        self.ui.editProfileYDestination.setText("")
        self.ui.editProfileZDestination.setText("")
        self.ui.SliderWidgetNeighbor.value = 0
        self.ui.SliderWidgetSteps.value = 0
        self.ui.profileOutputFilePathLineEdit.setCurrentPath("")
        self.ui.profileFilePathLineEdit.setCurrentPath("")
        
    def onResizeButton(self):
        """"
        Handles the event triggered by clicking the resize button.

        This method checks if all necessary input conditions are met before 
        proceeding with the resizing operation of a 3D file. If any conditions 
        are not satisfied, it displays a warning message to the user.    

        Returns:
        None

        Raises:
        Displays warning messages using `slicer.util.warningDisplay` if any input 
        requirements are not fulfilled.

        """
        print("Button resize clicked")
        print("onResizeButton self.logic.fileDirectory = ", self.logic.fileDirectory)
        if self.logic.fileDirectory == "no": 
            slicer.util.warningDisplay("Please select an input Directory or Add file!\n")
            return
        if (self.logic.fileDirectory == "d" or self.logic.fileDirectory == "no") and self.logic.inputDirectory is None: 
            slicer.util.warningDisplay("Please select an input directory!\n")
            return
        if self.logic.fileDirectory == "f" and self.logic.inputFile is None: 
            slicer.util.warningDisplay("Please select an input file!\n")
            return
        if not self.logic.outputFileResized: 
            slicer.util.warningDisplay("Please select an 3D resized output file!\n")
            return
        if not self.logic.programDirectory:
            slicer.util.warningDisplay("Please select a program directory!\n")
            return
        
        print("onResizeButton self.logic.beginSlice = ", self.logic.beginSlice)
        print("onResizeButton self.logic.endSlice = ", self.logic.endSlice)
        print("onResizeButton self.logic.sliderFactorResizeValue = ", self.logic.sliderFactorResizeValue)
        print("onResizeButton self.logic.outputFileResized = ", self.logic.outputFileResized)
        if self.logic.fileDirectory == "d":
            self.logic.create3DFileResized(self.logic.beginSlice, self.logic.endSlice, self.logic.inputDirectory, self.logic.sliderFactorResizeValue, self.logic.outputFileResized)  
        
    def onZoomButton(self):
        """"
        Handles the event triggered by clicking the zoom button.

        This method performs the following operations when the zoom button is clicked:
        1. Retrieves the selected zoom levels from the combo boxes in the user interface.
        2. Validates that the user has made valid selections for both zoom levels.
        3. Displays warning messages if the selections are invalid or if the program directory is not set.
        4. Based on the selected zoom levels, determines the appropriate path and name for the zoom parameters.
        5. Calls the `create3DFileResized` method to resize the 3D file according to the selected zoom level and parameters.
        6. Opens the resized file and updates the input volume file name and image size information.    

        Returns:
        None

        Raises:
        Displays warning messages using `slicer.util.warningDisplay` if any input 
    r   equirements are not fulfilled, such as unselected zoom levels or missing program directory.
        """
        print("Button zoom clicked")
        print("onZoomButton self.ui.comboBoxZoom1.currentText = ", self.ui.comboBoxZoom1.currentText)                
        index1 = self.ui.comboBoxZoom1.currentIndex
        print("onZoomButton index1 = ", index1)
        print("onZoomButton self.ui.comboBoxZoom2.currentText = ", self.ui.comboBoxZoom2.currentText)                
        index2 = self.ui.comboBoxZoom2.currentIndex
        print("onZoomButton index2 = ", index2)
        if index1 == -1 or index2 == -1:
            return
        if index1 == 0:
            print("No level 1 of zoom selected.")
            slicer.util.warningDisplay("Please select a level1 of zoom!\n")
            exit
        if not self.logic.programDirectory:
            slicer.util.warningDisplay("Please select a program directory!\n")
            return
        begin =0
        end =0
        factorResize =32
        if index2 ==0:
            print("Only level 1 of zoom selected.")            
            for zoom8um in self.logic.paramZoom["8um"]:
                if zoom8um["Name"] == self.ui.comboBoxZoom1.currentText:
                    name = zoom8um["Name"]
                    print("zoom8um path = ", zoom8um["path"])
                    path = zoom8um["path"]            
        else:
            print("level 2 of zoom selected.")
            for zoom8um in self.logic.paramZoom["8um"]:
                if zoom8um["Name"] == self.ui.comboBoxZoom1.currentText:
                    for zoom2um in zoom8um["2um"]:
                        if zoom2um["Name"] == self.ui.comboBoxZoom2.currentText:
                            name = zoom2um["Name"]
                            print("zoom2um path = ", zoom2um["path"])
                            path = zoom2um["path"]
                            break

        
        outputFile = self.logic.directoryTemp + name + ".nrrd"
        end = self.logic.retrieveSizeDirectory(path)
        print("self.logic.create3DFileResized(", begin," ,", end," ,", path,", ", factorResize,", ", outputFile, ")")
        res = self.logic.create3DFileResized(begin, end, path, factorResize, outputFile)
        if res == -1:
            return
        self.openFile(outputFile)
        self.logic.inputVolumeFileName = self.ui.inputVolumeSelector.currentNode().GetStorageNode().GetFileName()
        print("onZoomButton self.logic.inputVolumeFileName = ", self.logic.inputVolumeFileName)
        self.logic.retrieveSizeImageNrrd()
        self.majFileInfo()
        

    def onProfileButton(self):
        """"
        Handles the event triggered by clicking the profile button.

        This method performs the following operations when the profile button is clicked:
        1. Prints the current values from the profile input fields and relevant logic properties for debugging.
        2. Validates that the user has selected an input volume and provided necessary profile parameters.
        3. Displays warning messages if any required inputs are missing or invalid.
        4. Computes a normal vector or direction vector based on the provided origin and destination coordinates.
        5. Calls the `computeProfile` method to generate a profile based on the specified parameters.   

        Returns:
        None

        Raises:
        Displays warning messages using `slicer.util.warningDisplay` if any input 
        requirements are not fulfilled, such as missing input volume, profile parameters, or vector selections.
        """
        print("onProfileButton")
        print("self.ui.editProfileX.text = ", self.ui.editProfileX.text)
        print("self.ui.editProfileY.text = ", self.ui.editProfileY.text)
        print("self.ui.editProfileZ.text = ", self.ui.editProfileZ.text)
        print("self.ui.editProfileXDestination.text = ", self.ui.editProfileXDestination.text)
        print("self.ui.editProfileYDestination.text = ", self.ui.editProfileYDestination.text)
        print("self.ui.editProfileZDestination.text = ", self.ui.editProfileZDestination.text)
        print("self.logic.sliderNeighbor = ", self.logic.sliderNeighbor)
        print("self.logic.sliderStep = ", self.logic.sliderStep)        
        print("self.logic.profileOutputFile = ", self.logic.profileOutputFile)
        print("self.logic.profileFileDirectory = ", self.logic.profileFileDirectory)
        print("self.logic.profileNormalDirection = ", self.logic.profileNormalDirection)
        if self.ui.inputVolumeSelector.currentNode() is None:
            slicer.util.warningDisplay("Please select an input volume!\n")
            return         
        if self.ui.editProfileX.text == "" or self.ui.editProfileY.text == ""  or self.ui.editProfileZ.text == "" : 
            slicer.util.warningDisplay("Please select a origin zone for the profile!\n")
            return
        if self.logic.profileNormalDirection == "d" and (self.ui.editProfileXDestination.text == "" or self.ui.editProfileYDestination.text == ""  or self.ui.editProfileZDestination.text == "") : 
            slicer.util.warningDisplay("Please select a destination zone for the profile!\n")
            return
        if self.logic.profileOutputFile is None: 
            slicer.util.warningDisplay("Please select an profile output file!\n")
            return
        if self.logic.profileFileDirectory == "no":            
            slicer.util.warningDisplay("Please select a File!\n")
            return
        if self.logic.profileNormalDirection == "no": 
            slicer.util.warningDisplay("Please select Normal vector  or Direction vector!\n")
            return
        
        x = int(self.ui.editProfileX.text)
        y = int(self.ui.editProfileY.text)
        z = int(self.ui.editProfileZ.text)
        if self.logic.profileNormalDirection == "n":            
            vector = self.logic.computeNormals(x,y,z)        
            vector[0] = -1 * vector[0]
            vector[1] = -1 * vector[1]
            vector[2] = -1 * vector[2]
        else:
            xD = int(self.ui.editProfileXDestination.text)
            yD = int(self.ui.editProfileYDestination.text)
            zD = int(self.ui.editProfileZDestination.text)
            vector, nbPoints = self.logic.computeDirection(x,y,z,xD,yD,zD)
            if self.logic.sliderStep == 0:
                self.logic.sliderStep = nbPoints
            print("onProfileButton nbPoints  = ",nbPoints)        
        self.logic.computeProfile(x,y,z, vector, self.logic.profileOutputFile)

    def onDisplayProfileButton(self):
        """"
        Handles the event triggered by clicking the display profile button.

        This method is called when the user clicks the display profile button in the 
        application's user interface.
        
         Calls the `displayProfile` method from the logic layer, passing the current
        profile file stored in `self.logic.profileFile`.    

        Returns:
        None
        """
        print("onDisplayProfileButton")
        self.logic.displayProfile(self.logic.profileFile)

    
    def onSaveImageProfile(self):
        """"
        Handles the event triggered by clicking the save Image Profile button.

        This method is called when the user clicks the save Image profile button in the 
        application's user interface.
        
         Calls the `saveImageProfile` method from the logic layer, passing the current
        profile file stored in `self.logic.profileFile`.    

        Returns:
        None
        """
        print("onSaveImageProfile")
        self.logic.saveImageProfile(self.logic.profileFile)
    
    def majOutputResizedInfo(self):
        """"
        Updates the output dimensions for resized images.

        This method calculates the dimensions of the output image after resizing based 
        on the input image size, the resize factor, and the number of slices. It then 
        updates the user interface with the computed dimensions required for resizing.
    
        Returns:
        None
        """
        print("majOutputResizedInfo")        
        if self.logic.fileDirectory == "f":
            return
        x = int(self.logic.sizeImageInputOrigin[0]/ self.logic.sliderFactorResizeValue)
        y = int(self.logic.sizeImageInputOrigin[1]/ self.logic.sliderFactorResizeValue)
        nbSlices = self.logic.endSlice - self.logic.beginSlice + 1
        z = int(nbSlices/ self.logic.sliderFactorResizeValue)
        msg = "(" + str(x) + ", " + str(y) + ", " + str(z) + ")"
        size, time = self.logic.computeSizeTimeResize(nbSlices, self.logic.sliderFactorResizeValue)
        timeMin  = int(time / 60)
        timeSec = time - timeMin*60
        msg = msg + "   " + str(size) + " Mo"
        self.ui.labelOutputDimension.setText(msg)

    def majFileInfo(self):
        """"
        Updates the displayed dimensions of the input volume image.

        This method retrieves the dimensions (width, height, and depth) of the input 
        volume image from the logic layer and updates the corresponding label in the 
        user interface to display these dimensions.    

        Returns:
        None
        """
        print("majFileInfo")
        sizeX = self.logic.sizeImageInputVolume[0]
        sizeY = self.logic.sizeImageInputVolume[1]
        sizeZ = self.logic.sizeImageInputVolume[2]
        msg = "(" + str(sizeX) + ", " + str(sizeY) + ", " + str(sizeZ) + ")"        
        self.ui.labelOutputDimension.setText(msg)

    def convertRasToIjk(self, x, y, z):
        """"
        Converts RAS (Right-Anterior-Superior) coordinates to IJK (Image Index) coordinates.

        This method takes a point defined in RAS coordinates and converts it to IJK 
        coordinates using the current volume node's transformation matrix. The conversion 
        is useful for mapping anatomical coordinates to image voxel coordinates.

        Parameters:
        - x (float): The X coordinate in RAS space.
        - y (float): The Y coordinate in RAS space.
        - z (float): The Z coordinate in RAS space.

        Returns:
        - (int, int, int): The IJK coordinates corresponding to the given RAS coordinates.
        Returns (-1, -1, -1) if the current volume node is not set.
        """
        print("convertRasToIjk")           
        volumeNode = self.ui.inputVolumeSelector.currentNode()
        if volumeNode is None:
            return -1,-1,-1
        volumeRasToIjk = vtk.vtkMatrix4x4()
        volumeNode.GetRASToIJKMatrix(volumeRasToIjk)
        point_Ijk = [0, 0, 0, 1]
        coord = [x,y,z]
        volumeRasToIjk.MultiplyPoint(np.append(coord,1.0), point_Ijk)
        point_Ijk = [ int(round(c)) for c in point_Ijk[0:3] ]
        return point_Ijk[0], point_Ijk[1], point_Ijk[2]

    def convertIjkToRas(self, x, y, z):
        """"
        Converts IJK (Image Index) coordinates to RAS (Right-Anterior-Superior) coordinates.

        This method takes a point defined in IJK coordinates and converts it to RAS 
        coordinates using the current volume node's transformation matrix. The conversion 
        is useful for mapping voxel indices to anatomical coordinates.

        Parameters:
        - x (int): The X coordinate in IJK space (voxel index).
        - y (int): The Y coordinate in IJK space (voxel index).
        - z (int): The Z coordinate in IJK space (voxel index).

        Returns:
        - (float, float, float): The RAS coordinates corresponding to the given IJK coordinates.
        """
        print("convertIjkToRas")
        volumeNode = self.ui.inputVolumeSelector.currentNode()
        ijkToRas = vtk.vtkMatrix4x4()
        volumeNode.GetIJKToRASMatrix(ijkToRas)
        position_Ijk = [x, y, z, 1]
        position_Ras = ijkToRas.MultiplyPoint(position_Ijk)
        r = position_Ras[0]
        a = position_Ras[1]
        s = position_Ras[2]
        return r, a, s


    def onCheckBoxZoomChanged(self):
        """"
        Handles the event when the zoom checkbox is changed.

        This method is triggered when the state of the zoom checkbox is modified. 
        It enables or disables zoom functionality based on the checkbox state and 
        validates necessary conditions, such as the selection of an input volume and 
        input directory.
    
        Raises:
        - Warning messages if:
            - No input volume is selected.
            - No input directory is provided.

        Returns:
        - None
        """
        print("onCheckBoxZoomChanged")        
        print("self.ui.checkBoxZoom.checked = ", self.ui.checkBoxZoom.checked)
        if self.ui.checkBoxZoom.checked:
            print("onCheckBoxZoomChanged self.logic.inputDirectory = ", self.logic.inputDirectory)            
            self.logic.zoom = True            
            if self.ui.inputVolumeSelector.currentNode() is None:
                slicer.util.warningDisplay("Please add a file and select it!\n")
                self.ui.checkBoxZoom.checked = False
                return
            if self.logic.inputDirectory is None or self.logic.inputDirectory == "": 
                self.ui.checkBoxZoom.checked = False
                slicer.util.warningDisplay("Please select an input directory!\n")
                return
            self.logic.saveJsonDirectoryZoom = self.logic.inputDirectory
            self.loadParamZoomFromJson(self.logic.inputDirectory, self.logic.saveJsonDirectoryZoom)
            self.drawAreaZoom()
        else:
            self.logic.zoom = False
            self.eraseAreaZoom()

    def drawAreaZoom(self):
        """"
         Draws zoom areas based on parameters loaded from a JSON file.

        This method checks if zoom parameters exist and then iterates through 
        the zoom regions defined in the JSON data. For each zoom region, it 
        calculates the center coordinates in both IJK and RAS space, creates 
        a region of interest (ROI) in the 3D view, and sets the display properties.        

        Returns:
        - None
        """
        print("drawAreaZoom")
        print("self.logic.zoomJsonExist = ", self.logic.zoomJsonExist)
        if not self.logic.zoomJsonExist:
            return
        i=0        
        self.logic.list8um.clear()
        self.logic.list8um.append("no selected area")        
        for zoom8um in self.logic.paramZoom["8um"]:
            self.logic.list8um.append(zoom8um["Name"])            
            centerX = zoom8um["center"][0]
            centerY = zoom8um["center"][1]
            centerZ = zoom8um["center"][2]
            centerR, centerA, centerS = self.convertIjkToRas(centerX, centerY, centerZ)
            centerX = int(centerX/self.logic.factorResize)
            centerY = int(centerY/self.logic.factorResize)
            centerZ = int(centerZ/self.logic.factorResize)
            centerR = int(centerR/self.logic.factorResize)
            centerA = int(centerA/self.logic.factorResize)
            centerS = int(centerS/self.logic.factorResize)
            self.logic.listAreaCenter.append([centerX, centerY, centerZ])            
            self.logic.markupsZoom.append(slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsROINode"))         
            self.logic.markupsZoom[i].GetDisplayNode().SetSelectedColor(1.0,0.0,0.0) # red        
            self.logic.markupsZoom[i].GetDisplayNode().SetPointLabelsVisibility(True)
            self.logic.markupsZoom[i].GetDisplayNode().SetVisibility(True)
            self.logic.markupsZoom[i].LockedOn() # it can't be modified     
            self.logic.markupsZoom[i].SetSize(int(400/self.logic.factorResize), int(600/self.logic.factorResize), int(200/self.logic.factorResize))
            self.logic.markupsZoom[i].SetCenter(centerR, centerA, centerS)            
            i = i+1
        self.addNameAreaZoom(self.logic.list8um, self.ui.comboBoxZoom1)
        
        
    def addNameAreaZoom(self, list, comboBox):
        """"
        Adds names of zoom areas to a specified combo box in the user interface.

        This method clears the existing items in the provided combo box 
        and populates it with a new list of area names.

        Parameters:
        - list (list of str): A list containing the names of the zoom areas to be added.
        - comboBox (QComboBox): The combo box widget in which the names will be displayed.

        Returns:
        - None
        """
        print("addNameAreaZoom")
        comboBox.clear()        
        comboBox.addItems(list)

    def onComboBoxZoom1Changed(self):
        """"
        Handles changes in the first zoom level combo box selection.

        This method is triggered when the selected item in the 
        combo box for zoom level 1 changes. It updates the slice offsets 
        based on the selected area and populates the second zoom level 
        combo box with corresponding names if applicable.  

        Returns:
        - None
        """
        print("onComboBoxZoom1Changed")
        print("onComboBoxZoom1Changed self.ui.comboBoxZoom1.currentText = ", self.ui.comboBoxZoom1.currentText)                
        index = self.ui.comboBoxZoom1.currentIndex
        if index > 0:            
            self.changeSliceOffset(2, "Red", self.logic.listAreaCenter[index-1][2])           
            self.changeSliceOffset(1, "Green", self.logic.listAreaCenter[index-1][1])            
            self.changeSliceOffset(0, "Yellow", self.logic.listAreaCenter[index-1][0])            
            self.logic.list2um.clear()
            self.ui.comboBoxZoom2.clear()
            self.logic.list2um.append("no selected area")    
            for zoom8um in self.logic.paramZoom["8um"]:
                if zoom8um["Name"] == self.ui.comboBoxZoom1.currentText:
                    for zoom2um in zoom8um["2um"]:
                        self.logic.list2um.append(zoom2um["Name"])
                        break
            self.addNameAreaZoom(self.logic.list2um, self.ui.comboBoxZoom2)
        else:
            self.ui.comboBoxZoom2.setCurrentIndex(0)      
        
    
    def onComboBoxZoom2Changed(self):
        """
        Handles changes in the second zoom level combo box selection.

        This method is triggered when the selected item in the 
        combo box for zoom level 2 changes. It is expected to update 
        the application state or UI based on the selected zoom area 
        from the second combo box.

        Not implemented, but should be when there will be several zoom level 2.

        Returns:
        - None
        """
        print("onComboBoxZoom2Changed")
    
    def eraseAreaZoom(self):
        """"
        Erases the current zoom area selections and associated markup nodes.

        This method clears the user interface elements related to zoom 
        areas and removes any existing markup nodes that are not 
        designated as essential (i.e., those that should remain). 
        Specifically, it does the following:

        1. Clears the items in the combo boxes for zoom levels 1 and 2.
        2. Clears the internal lists that hold zoom area information.
        3. Removes any existing markup nodes of type "vtkMRMLMarkupsROINode"
        from the scene, except for those with specific IDs that should 
        be preserved (e.g., profile markup nodes).
        4. Empties the list that tracks markup nodes associated with zoom areas.

        Returns:
        - None
        """
        print("eraseAreaZoom")        
        self.ui.comboBoxZoom1.clear()
        self.ui.comboBoxZoom2.clear()
        self.logic.list8um.clear()
        self.logic.list2um.clear()        
        self.logic.listAreaCenter.clear()      
        existingMarkupsZoom = slicer.util.getNodesByClass("vtkMRMLMarkupsROINode")        
        for markupsZoomItem in existingMarkupsZoom:
            if markupsZoomItem.GetID() != self.markupsNodeId and markupsZoomItem.GetID() != self.profileMarkupsNodeIdOrigin and markupsZoomItem.GetID() != self.profileMarkupsNodeIdDestination: # don't erase ROI markup  and Profile markup              
                slicer.mrmlScene.RemoveNode(markupsZoomItem)
        self.logic.markupsZoom.clear()        

    
    def onOpenFileButton(self):
        """"
        Handles the action triggered by the "Open File" button.

        This method is called when the user clicks the "Open File" button 
        in the user interface. It performs the following actions:

        1. Checks if an input file has been selected. If not, displays 
        a warning message to the user and returns early.
        2. Calls the `openFile` method to open the selected input file.
        3. Retrieves the file name of the currently selected volume node 
        in the input volume selector and stores it in 
        `self.logic.inputVolumeFileName`.
        4. Logs the file name of the input volume to the console.
        5. Calls `retrieveSizeImageNrrd` to obtain size information 
        related to the NRRD image.
        6. Updates the file information displayed in the user interface 
        by calling `majFileInfo`.

        Returns:
        - None
        """
        print("Button Open file clicked")
        if self.logic.inputFile is None:
            slicer.util.warningDisplay("Please select an input file!\n")
            return
        self.openFile(self.logic.inputFile)
        self.logic.inputVolumeFileName = self.ui.inputVolumeSelector.currentNode().GetStorageNode().GetFileName()
        print("onOpenFileButton self.logic.inputVolumeFileName = ", self.logic.inputVolumeFileName)
        self.logic.retrieveSizeImageNrrd()
        self.majFileInfo()

    def onradioButtonFile(self):
        print("onradioButtonFile checked")
        self.logic.fileDirectory = "f"
        print("onradioButtonFile self.logic.fileDirectory = ", self.logic.fileDirectory )


    def onradioButtonDirectory(self):
        """"
        Handles the action triggered by selecting the directory radio button.

        This method is called when the user checks the radio button 
        indicating that the file input will be a directory. It performs 
        the following actions:

        1. Sets the `fileDirectory` attribute in the logic layer to "d", 
        indicating that the input type is a directory.
        2. Logs the updated value of `self.logic.fileDirectory` to the console.

        Returns:
        - None
        """
        print("onradioButtonDirectory checked")
        self.logic.fileDirectory = "d"
        print("onradioButtonDirectory self.logic.fileDirectory = ", self.logic.fileDirectory )
    
    def openFile(self, inputFile):
        """"
        Opens a specified file and updates the UI and logic states accordingly.

        This method is responsible for loading a volume file into the application 
        and updating the relevant user interface elements and internal logic states 
        to reflect the currently loaded file. The following actions are performed:

        1. Sets the `fileDirectory` attribute in the logic layer to "f", 
            indicating that a file (as opposed to a directory) has been selected.
        2. Loads the specified volume file using the `slicer.util.loadVolume` method.
        3. Updates the input volume selector UI element to reflect the loaded volume node.
        4. Checks the radio button for file input in the UI.
        5. Sets the internal state for `factorResize` to 1, indicating no resizing.
        6. Sets the `profileFileDirectory` attribute to "f", indicating that a file is being used.

        Args:
            inputFile (str): The path to the volume file to be opened.

        Returns:
        None
        """
        print("openfile")
        self.logic.fileDirectory = "f"  
        loadedVolumeNode = slicer.util.loadVolume(inputFile)        
        self.ui.inputVolumeSelector.setCurrentNode(loadedVolumeNode)               
        self.ui.radioButtonFile.setChecked(True)
        self.radioButtonFile = True        
        self.radioButtonDirectory = False        
        self.logic.factorResize = 1        
        self.logic.profileFileDirectory = "f"
    
        
    def onradioButtonProfileNormal(self):
        """"
        Handles the event when the "Profile Normal" radio button is checked.

        This method is triggered when the user selects the "Profile Normal" 
        radio button in the UI. It updates the internal logic state to indicate 
        that the profile normal direction is to be used in subsequent computations. 
        This affects how profiles are calculated and drawn within the application.

        Actions performed:
        - Sets the `profileNormalDirection` attribute in the logic layer to "n", 
        signifying that the normal vector should be utilized.

        Returns:
            None
        """
        print("onradioButtonProfileNormal checked")
        self.logic.profileNormalDirection = "n"
        print("onradioButtonProfileNormal self.logic.profileNormalDirection = ", self.logic.profileNormalDirection )


    def onradioButtonProfileDirection(self):
        """
        Handles the event when the "Profile Direction" radio button is checked.

        This method is triggered when the user selects the "Profile Direction" 
        radio button in the UI. It updates the internal logic state to indicate 
        that the profile direction vector is to be used in subsequent computations. 
        This affects how profiles are calculated and drawn within the application.

        Actions performed:
        - Sets the `profileNormalDirection` attribute in the logic layer to "d", 
        signifying that the direction vector should be utilized instead of the normal vector.

        Returns:
            None
        """
        print("onradioButtonProfileDirection checked")
        self.logic.profileNormalDirection = "d"
        print("onradioButtonProfileDirection self.logic.profileNormalDirection = ", self.logic.profileNormalDirection )

    def onradioButtonProfileMean(self):
        """"
        Handles the event when the "Profile Mean" radio button is checked.

        This method is triggered when the user selects the "Profile Mean" radio button 
        in the UI. It updates the internal logic state to indicate that the mean value 
        should be used for profile measurements in subsequent computations.

        Actions performed:
        - Sets the `profileMeasurement` attribute in the logic layer to "m", 
        signifying that the mean profile measurement will be used for further analysis.

        Returns:
            None
        """
        print("onradioButtonProfileMean checked")
        self.logic.profileMeasurement = "m"
        print("onradioButtonProfileMean self.logic.profileMeasurement = ", self.logic.profileMeasurement )

    def onradioButtonProfileMedian(self):
        """"
        Handles the event when the "Profile Median" radio button is checked.

        This method is triggered when the user selects the "Profile Median" radio button 
        in the UI. It updates the internal logic state to indicate that the median value 
        should be used for profile measurements in subsequent computations.

        Actions performed:
        - Sets the `profileMeasurement` attribute in the logic layer to "d", 
        indicating that the median profile measurement will be utilized for further analysis.

        Returns:
            None
        """
        print("onradioButtonProfileMedian checked")
        self.logic.profileMeasurement = "d"
        print("onradioButtonProfileMedian self.logic.profileMeasurement = ", self.logic.profileMeasurement )

    def onradioButtonProfileMin(self):
        """"
        Handles the event when the "Profile Minimum" radio button is checked.

        This method is triggered when the user selects the "Profile Minimum" radio button 
        in the user interface. It updates the internal state to indicate that the minimum 
        value should be used for profile measurements in subsequent analyses.

        Actions performed:
        - Sets the `profileMeasurement` attribute in the logic layer to "n", 
        indicating that the minimum profile measurement will be utilized for further processing.

        Returns:
            None
        """
        print("onradioButtonProfileMin checked")
        self.logic.profileMeasurement = "n"
        print("onradioButtonProfileMin self.logic.profileMeasurement = ", self.logic.profileMeasurement )
    
    def onradioButtonProfileMax(self):
        """"
        Handles the event when the "Profile Maximum" radio button is checked.

        This method is triggered when the user selects the "Profile Maximum" radio button 
        in the user interface. It updates the internal state to indicate that the maximum 
        value should be used for profile measurements in subsequent analyses.

        Actions performed:
        - Sets the `profileMeasurement` attribute in the logic layer to "x", 
        indicating that the maximum profile measurement will be utilized for further processing.

        Returns:
            None
        """
        print("onradioButtonProfileMax checked")
        self.logic.profileMeasurement = "x"
        print("onradioButtonProfileMax self.logic.profileMeasurement = ", self.logic.profileMeasurement )
    
    def onradioButtonProfileBlock(self):
        """"
        Handles the event when the "Profile Block" radio button is checked.

        This method is triggered when the user selects the "Profile Block" radio button 
        in the user interface. It updates the internal state to specify that the profile 
        type is set to block mode for subsequent analyses.

        Actions performed:
        - Sets the `profileTypeBlock` attribute in the logic layer to "3", 
        indicating that the block profile type will be used in further processing.

        Returns:
            None
        """
        print("onradioButtonProfileBlock checked")
        self.logic.profileTypeBlock = "3"
        print("onradioButtonProfileBlock self.logic.profileTypeBlock = ", self.logic.profileTypeBlock )

    def onradioButtonProfilePlan(self):        
        """"
        Handles the event when the "Profile Plan" radio button is checked.

        This method is triggered when the user selects the "Profile Plan" radio button 
        in the user interface. It updates the internal state to specify that the profile 
        type is set to plan mode for subsequent analyses.

        Actions performed:
        - Sets the `profileTypeBlock` attribute in the logic layer to "2", 
        indicating that the plan profile type will be used in further processing.

        Returns:
            None
        """
        print("onradioButtonProfilePlan checked")
        self.logic.profileTypeBlock = "2"
        print("onradioButtonProfileBlock self.logic.profileTypeBlock = ", self.logic.profileTypeBlock )

    
    # end code Olivier

#
# t_ZoomRoiLogic
#


class t_ZoomRoiLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self) -> None:
        """Called when the logic class is instantiated. Can be used for initializing member variables."""
        ScriptedLoadableModuleLogic.__init__(self)
        # begin code Olivier
        self.inputVolume = None
        self.inputVolumeFileName = None      
        self.inputDirectory = None
        self.inputFile = None
        self.createdRoi = False        
        self.outputFile = None
        self.saveJsonDirectory = "./saveParam/"        
        self.saveJsonDirectoryZoom = None
        self.inputVolumeBefore = None
        self.beginSlice = None
        self.endSlice = None
        self.outputFileResized = None
        self.sliderFactorResizeValue = 1
        self.zoom = False
        self.paramZoom = None
        self.markupsZoom = []
        self.list8um = []        
        self.list2um = []
        self.listAreaCenter = []
        self.zoomJsonExist = False
        self.fileDirectory = "no"
        self.directoryTemp = "./saveParam/temp/"
        self.inputDirectoryExtension = "jp2"        
        self.programDirectory = None
        self.resizeImageProgram = "resizeImageParall"
        self.createRoiProgram = "createRoiImage3D"
        self.computeProfileProgram = "computeProfile"
        self.displayProfileProgram = "displayProfile"
        self.pythonProgram = "python3"
        self.directoryConfig = ".citrusSkin"
        self.fileConfig = "configuration.json"
        self.factorResize = None
        self.sliderNeighbor = 0
        self.sliderStep = 0
        self.profileOutputFile = None
        self.profileFile = None
        self.profileFileDirectory = "no"
        self.profileNormalDirection = "no"
        self.profileMeasurement = "no"
        self.profileTypeBlock = "3"

        # end code Olivier

    def getParameterNode(self):
        return t_ZoomRoiParameterNode(super().getParameterNode())

    def process(self,
                inputVolume: vtkMRMLScalarVolumeNode,
                outputVolume: vtkMRMLScalarVolumeNode,
                imageThreshold: float,
                invert: bool = False,
                showResult: bool = True) -> None:
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param inputVolume: volume to be thresholded
        :param outputVolume: thresholding result
        :param imageThreshold: values above/below this threshold will be set to 0
        :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
        :param showResult: show output volume in slice viewers
        """

        if not inputVolume or not outputVolume:
            raise ValueError("Input or output volume is invalid")

        import time

        startTime = time.time()
        logging.info("Processing started")

        # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
        cliParams = {
            "InputVolume": inputVolume.GetID(),
            "OutputVolume": outputVolume.GetID(),
            "ThresholdValue": imageThreshold,
            "ThresholdType": "Above" if invert else "Below",
        }
        cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True, update_display=showResult)
        # We don't need the CLI module node anymore, remove it to not clutter the scene with it
        slicer.mrmlScene.RemoveNode(cliNode)

        stopTime = time.time()
        logging.info(f"Processing completed in {stopTime-startTime:.2f} seconds")
    
    # begin code Olivier


    def createRoi(self, center, size):
        """
        Create a Region of Interest (ROI) based on a specified center and size
        and run an external program to process the ROI.

        The function resizes the center and size of the ROI based on a predefined resize factor, ensures 
        the dimensions are even, checks if the ROI fits within the image boundaries, and calls an external 
        program to perform further computations.

        Parameters:
        center (list of int ): A list of 3 coordinates representing the center of the ROI in the 
                                   format [x, y, z].
        size (list of int): A list of 3 values representing the dimensions of the ROI in the 
                                 format [width, height, depth].
        """
        print("create ROI")
        print("center = ", center)
        print("size = ", size)
        center[0] = round(center[0] * self.factorResize)        
        center[1] = round(center[1] * self.factorResize)
        center[2] = round(center[2] * self.factorResize)
        size[0] = round(size[0] * self.factorResize)              
        size[1] = round(size[1] * self.factorResize)
        size[2] = round(size[2] * self.factorResize)
        if size[0] %2  == 1:
            size[0] = size[0]+1
        if size[1] % 2 == 1:
            size[1] = size[1]+1
        if size[2] % 2 == 1:
            size[2] = size[2]+1  
        print("logic.createRoi center = ", center)
        print("logic.createRoi size = ", size)        
        difX = center[0]-size[0]/2
        difY = center[1]-size[1]/2
        difZ = center[2]-size[2]/2
        somX = center[0]+size[0]/2
        somY = center[1]+size[1]/2
        somZ = center[2]+size[2]/2        
        if difX < 0 or difY <0 or difZ <0 or somX > self.sizeImageInputOrigin[0] or somY > self.sizeImageInputOrigin[1] or somZ > self.sizeZImageInputOrigin:
            msg = "The ROI is outside of the image!"                 
            slicer.util.messageBox(msg)
            return
        sizeRoi, timeRoi = self.computeSizeTimeRoi(size)
        min = int(timeRoi/60)
        sec = timeRoi-min*60
        msg = "Size of the ROI " + str(sizeRoi) + " Mo.\nDo you want to continue?"
        print(msg)
        print(self.programDirectory + "/" + self.createRoiProgram + " " + self.inputDirectory + "/ " + str(size[0]) + " " + str(size[1]) + " " +  str(size[2]) + " " + str(center[0]) + " " +  str(center[1]) + " " +  str(center[2]) + " c" + " " + self.outputFile + " 1" + " " + self.inputDirectoryExtension)               
        if not slicer.util.confirmYesNoDisplay(msg):
            return
        if not os.path.exists(self.programDirectory + "/" + self.createRoiProgram):
            slicer.util.warningDisplay(self.programDirectory + "/" + self.createRoiProgram + " does not exist!\n")
            return
        result = subprocess.run([self.programDirectory + "/" + self.createRoiProgram, self.inputDirectory + "/", str(size[0]), str(size[1]), str(size[2]), str(center[0]), str(center[1]), str(center[2]), "c", self.outputFile, "1", self.inputDirectoryExtension], capture_output=True, text=True)        
        print("stdout:", result.stdout)
        print("stderr:", result.stderr)

    def retrieveSizeImage(self):
        """
        Retrieve the dimensions of the input image volume from the specified directory and handle NRRD files.

        This function reads image files from the input directory, processes the directory contents, and 
        retrieves the size of the input image. If the input volume is a NRRD file, it delegates the retrieval 
        to the `retrieveSizeImageNrrd` method. The method also handles file extensions and sorts directory 
        contents for further processing.

        Parameters:
        None

        Returns:
        None: The function prints status messages and updates internal attributes like `self.sizeImageInputOrigin`, 
          which stores the dimensions of the image, and `self.sizeZImageInputOrigin`, which refers to the z-dimension.

        Attributes Modified:
        - `self.dirList`: List of files in the input directory, sorted and cleaned based on the file extension.
        - `self.inputDirectoryExtension`: The extension of the input image files (e.g., `.nrrd`, `.nii`).
        - `self.sizeImageInputOrigin`: The size (dimensions) of the first image file in the directory.
        - `self.sizeZImageInputOrigin`: The z-dimension of the input image.

        Exceptions:
        - If the input volume or input filename is set and is a NRRD file, the method will call `retrieveSizeImageNrrd`.
        - If there is an issue reading the directory or the input image, an error message is printed 
          specifying the exception encountered.
        """
        print("retrieveSizeImage")        
        if self.inputVolume is not None and self.inputVolumeFileName is not None:            
            self.retrieveSizeImageNrrd()
        
        try:
            self.dirList = os.listdir(self.inputDirectory)
            self.dirList.sort()
            self.inputDirectoryExtension = self.retrieveExtension(self.inputDirectory, self.dirList) 
            self.dirList = self.cleanList(self.inputDirectory, self.dirList, self.inputDirectoryExtension)
            self.sizeZImageInputOrigin = len(self.dirList)
            print("dirList[0] = ", self.dirList[0])
            print("dirList[0] = ", self.inputDirectory + "/" + self.dirList[0])
            imageInputOrigin = sitk.ReadImage(self.inputDirectory + "/" + self.dirList[0])
            self.sizeImageInputOrigin = imageInputOrigin.GetSize()
            print("self.sizeImageInputOrigin = ", self.sizeImageInputOrigin)       
            print("self.sizeZImageInputOrigin = ", self.sizeZImageInputOrigin)        
                
        except Exception as e:
            print("Can't read input Origin image", str(e))
    
    def cleanList(self, inputDirectory,list, inputDirectoryExtension):
        """
        Filters a list of files in the input directory based on the specified file extension.

        This function iterates through the list of files and keeps only those that match the given 
        file extension. It constructs the full path of each file and compares its extension to 
        the `inputDirectoryExtension` parameter.

        Parameters:
        inputDirectory (str): The directory where the files are located.
        list (list of str): A list of filenames to be filtered.
        inputDirectoryExtension (str): The file extension (without the dot) to filter by (e.g., 'jp2').

        Returns:
        list of str: A new list containing only the filenames that have the specified extension.
        """
        print("cleanList")
        listTemp = []
        for item in list:
            split = os.path.splitext(inputDirectory + item)
            extension = split[1]           
            if extension == ("." + inputDirectoryExtension):
                listTemp.append(item)        
        return listTemp
        
    def retrieveExtension(self, inputDirectory, list):
        """
        Determines the most common file extension in a list of files from the input directory.

        This function scans the provided list of filenames, extracts their extensions, and counts 
        how many times each extension appears. It returns the extension that occurs the most frequently.

        Parameters:
        inputDirectory (str): The directory where the files are located.
        list (list of str): A list of filenames from which to retrieve and count extensions.

        Returns:
        str: The most common file extension found in the list (without the leading dot).
        """
        print("retrieveExtension")
        extension = "jp2"
        extensions = {}
        for item in list:
            split = os.path.splitext(inputDirectory + item)
            extension = split[1]
            extension = extension[1:]            
            if extension in extensions:
                extensions[extension] += 1
            else:
                extensions[extension] = 1        
        max =0
        extension = ""
        for key, value in extensions.items():
            if value > max:
                max = value
                extension = key        
        print("retrieveExtension extension", extension)
        return extension
    
    def retrieveSizeImageNrrd(self):
        """
        Retrieves the size (dimensions) of an NRRD image file from the input volume filename.

        This function reads the NRRD image specified by `self.inputVolumeFileName`, extracts its dimensions, 
        and stores them in `self.sizeImageInputVolume`. If the file cannot be read, an error message is printed.

        Parameters:
        None

        Returns:
        None: The function prints the image size and updates the `self.sizeImageInputVolume` attribute with 
              the dimensions of the NRRD image.

        Attributes Modified:
        - `self.sizeImageInputVolume`: Stores the size (dimensions) of the input NRRD volume.

        Exceptions:
        - If there is an issue reading the NRRD file (e.g., file not found, invalid format), an exception is 
        caught and an error message is printed.
        """
        print("retrieveSizeImageNrrd")
        print("retrieveSizeImageNrrd self.inputVolumeFileName = ", self.inputVolumeFileName)
        try:
            imageInputVolume = sitk.ReadImage(self.inputVolumeFileName)
            self.sizeImageInputVolume = imageInputVolume.GetSize()
            print("retrieveSizeImageNrrd self.sizeImageInputVolume = ", self.sizeImageInputVolume)            
        except Exception as e:
            print("Can't read input Volume image", str(e))
    
    def retrieveSizeDirectory(self, inputDirectory):
        """
        Retrieves the number of image slices (Z-dimension) in the specified input directory.

        This function lists the files in the input directory, filters them by the most common extension, 
        and calculates the number of image slices based on the number of files in the directory. 
        The last slice index is returned.

        Parameters:
        inputDirectory (str): The directory containing image slices to be processed.

        Returns:
        int: The index of the last image slice (Z-dimension), which is the total number of slices minus one.

        Attributes Modified:
        - `self.inputDirectoryExtension`: The most common file extension found in the directory.
        - `self.sizeZImageInputOrigin`: The number of image slices (Z-dimension) in the directory.

        Exceptions:
        - If there is an issue reading the directory or filtering the files (e.g., the directory doesn't exist 
        or contains unsupported file types), an exception is caught and an error message is printed.
        """
        print("retrieveSizeDirectory")
        lastSlice =0
        try:
            dirList = os.listdir(inputDirectory)
            dirList.sort()
            self.inputDirectoryExtension = self.retrieveExtension(self.inputDirectory, self.dirList) 
            dirList = self.cleanList(inputDirectory, dirList, self.inputDirectoryExtension)         
            sizeZImageInputOrigin = len(dirList)
            print("dirList[0] = ", dirList[0])
            print("dirList[0] = ", inputDirectory + "/" + dirList[0])            
            lastSlice =  sizeZImageInputOrigin-1 
            print("retrieveSizeDirectory lastSlice = ", lastSlice)                  
        except Exception as e:
            print("Can't read input Origin image", str(e))
        return lastSlice

    
    def computeFactorResize(self):
        """
        Computes the resize factor between the original image size and the input volume size.

        This function calculates the ratio between the width (X-dimension) of the original input image and 
        the input volume image. The result is rounded to the nearest integer and stored in the `self.factorResize` 
        attribute.

        Parameters:
        None

        Returns:
        None: The function updates the `self.factorResize` attribute with the computed resize factor.

        Attributes Modified:
        - `self.factorResize`: Stores the ratio of the width (X-dimension) between the original image size 
        (`self.sizeImageInputOrigin[0]`) and the input volume size (`self.sizeImageInputVolume[0]`).
        """
        self.factorResize = round(self.sizeImageInputOrigin[0]/self.sizeImageInputVolume[0])
        print("self.factorResize = ", self.factorResize)
        
    def computeSizeTimeRoi(self,sizeRoi):
        time = sizeRoi[2] * self.sizeImageInputOrigin[0] * self.sizeImageInputOrigin[1] * 0.000000072  # estimation  pour décompresser et charger une image  
        #time = sizeRoi[2] * 1.0  # TODO trouver une bonne estimation , estimation  pour décompresser et charger une image      
        size = sizeRoi[0] * sizeRoi[1] * sizeRoi[2] * 4 /(1000*1000) # en Mo
        return round(size), round(time)
    
    def computeSizeTimeResize(self, nbSlices, factorResize):
        time = nbSlices / factorResize * 1.0 # estimation 1s pour charger et parcourir une image 
        size = self.sizeImageInputOrigin[0] * self.sizeImageInputOrigin[1] * 4 * nbSlices /(factorResize * factorResize * factorResize * (1000*1000))
        return round(size), round(time)
    
    def computeTime(self, sizeX, sizeY, sizeZ, factorResize): # TODO à vérifier pour la rendre générique
        time = sizeZ * sizeX * sizeY * 0.000000072  # estimation  pour décompresser et charger une image  
        size = sizeX * sizeY * 4 * sizeZ /(factorResize * factorResize * factorResize * (1000*1000))
        return round(size), round(time)
    
    def displayJsonData(self):
        """
        Displays the key-value pairs stored in the class's dictionary attribute.

        This function iterates through the `self.dictionary` attribute, which is expected to hold 
        JSON-like data, and prints each key along with its corresponding value.

        Parameters:
        None

        Returns:
        None: The function prints each key-value pair in the dictionary to the console.

        Attributes Accessed:
        - `self.dictionary`: A dictionary containing the data to be displayed, with keys representing 
        data fields and values representing their associated values.
        """
        print("displayJsonData")
        for key, value in self.dictionary.items():
            print("key = ", key, ", value = ", value)
    
    def create3DFileResized(self, begin, end, inputDirectory, factorResize, outputFile) :
        """
        Creates a resized 3D image file by processing image slices from the input directory.

        This function processes a subset of image slices, specified by the `begin` and `end` indices, and resizes 
        them by a given `factorResize`. It estimates the size for the resized 3D image, asks 
    f   or user confirmation, and then calls an external program to create the resized 3D image file.

        Parameters:
        begin (int): The index of the first slice to be processed.
        end (int): The index of the last slice to be processed.
        inputDirectory (str): The directory containing the image slices.
        factorResize (float): The resize factor applied to the slices.
        outputFile (str): The path where the output 3D image file will be saved.

        Returns:
        int: Returns 0 on success, or -1 if the process is aborted or an error occurs.

        Attributes Accessed:
        - `self.programDirectory`: The directory containing the external resizing program.
        - `self.resizeImageProgram`: The name of the external program to perform the resizing.
        - `self.inputDirectoryExtension`: The file extension of the input image slices.
        - `self.fileDirectory`: Determines whether the process involves a directory ('d') or a file ('f').

        Exceptions:
        - If the user does not confirm the operation, the function exits early with a return value of -1.
        - If the external resizing program is missing, an error message is displayed and the function returns -1.
        """
        print("create3DFileResized")
        print(str(begin) + " " + str(end) + " " +  str(factorResize) + " " + outputFile)
        nbSlices = end-begin+1
        sizeRoi, timeRoi = self.computeSizeTimeResize(nbSlices, factorResize)
        min = int(timeRoi/60)
        sec = timeRoi-min*60
        msg = "Size of the 3D file " + str(sizeRoi) + " Mo.\nDo you want to continue?"
        print(msg)        
        print(self.programDirectory + "/" + self.resizeImageProgram + " " + inputDirectory + "/ " + str(begin) + " " + str(end) + " " + str(factorResize) + " " + outputFile + " " + self.inputDirectoryExtension)        
        if not slicer.util.confirmYesNoDisplay(msg):
            return -1
        if not os.path.exists(self.programDirectory + "/" + self.resizeImageProgram):
            slicer.util.warningDisplay(self.programDirectory + "/" + self.resizeImageProgram + " does not exist!\n")
            return  -1   
        if self.fileDirectory == "d":            
            result = subprocess.run([self.programDirectory + "/" + self.resizeImageProgram, inputDirectory + "/", str(begin), str(end), str(factorResize), outputFile, self.inputDirectoryExtension], capture_output=True, text=True)        
        elif self.fileDirectory == "f":
            print("create3DFileResized resize from file")
        else:
            print("create3DFileResized select Directory or File")
        print("stdout:", result.stdout)
        print("stderr:", result.stderr)
        return 0 

    def createDirectory(self, directory, varDirectory):
        """
        Creates a new directory in the user's home directory if it does not already exist.

        This function checks for the existence of a specified directory within the user's home directory. 
        If the directory does not exist, it creates the directory. The full path of the newly created 
        (or existing) directory is then assigned to `varDirectory`.

        Parameters:
        directory (str): The name of the directory to be created within the user's home directory.
        varDirectory (str): A variable to hold the full path of the created directory.

        Returns:
        str: The full path of the created or existing directory.
        """
        print("createDirectory")
        if not os.path.exists(os.getenv("HOME") + "/" + directory):
            os.makedirs(os.getenv("HOME") + "/" + directory)
        varDirectory = os.getenv("HOME") + "/" + directory
        print("createDirectory varDirectory = ", varDirectory)
        return varDirectory
    
    def eraseFilesJson(self, directorySaveParam):
        """
        Erases all JSON files in the specified directory.

        It invokes `self.eraseFiles`, passing the directory path and the file extension ("json") 
        to perform the deletion.

        Parameters:
        directorySaveParam (str): The path of the directory from which JSON files will be deleted.

        Returns:
        None: The function does not return any value but performs file deletion.        
        """
        print("eraseFilesJson")
        print("eraseFilesJson directorySaveParam = ", directorySaveParam)        
        self.eraseFiles(directorySaveParam, "json")

    def eraseFilesTmp(self, directoryTemp):
        """
        Erases all temporary files in the specified temporary directory.

        It invokes `self.eraseFiles`, passing the directory path and the keyword "all" to specify 
        that all files should be removed

        Parameters:
        directoryTemp (str): The path of the temporary directory from which all files will be deleted.

        Returns:
        None: The function does not return any value but performs file deletion.    
        """
        print("eraseFilesTmp")
        self.eraseFiles(directoryTemp, "all")

    def eraseFiles(self, directory, patternExtension):
        """
        Erases files in the specified directory that match a given extension pattern.

        This function lists all files in the specified `directory`, sorts them, and removes those 
        that match the specified file extension pattern.

        Parameters:
        directory (str): The path of the directory from which files will be deleted.
        patternExtension (str): The file extension pattern to match for deletion.
                                Use "all" to delete all files regardless of their extension.

        Returns:
        None: The function does not return any value but performs file deletion.    
        """
        print("eraseFiles")
        listFiles = os.listdir(directory)
        print("eraseFiles listFiles = ", listFiles)
        listFiles.sort()
        print("eraseFiles listFiles sorted= ", listFiles)
        for file in listFiles:
            if  os.path.isfile(directory + file):
                print("file = ", file)
                split = os.path.splitext(directory + file)
                extension = split[1]
                print("extension = ", extension)
                if patternExtension == "all" or  extension == "." + patternExtension:
                    os.remove(directory + file)
        listFiles = os.listdir(directory)
        print("eraseFiles listFiles after remove = ", listFiles)   


    def loadConfiguration(self):
        """
         Loads the configuration from a JSON file, creating the necessary directories and 
        default configuration if the file does not exist.

        This function checks for the existence of a specified configuration directory and 
        configuration file within the user's home directory. If the directory or file 
        does not exist, it creates them and initializes the configuration with default values.

        Returns:
        None: The function does not return any value but sets the class attributes based on 
        the loaded configuration.
        """
        print("loadConfiguration")        
        print("rep = ", os.getenv("HOME") + "/" + self.directoryConfig)
        if not os.path.exists(os.getenv("HOME") + "/" + self.directoryConfig):
            os.makedirs(os.getenv("HOME") + "/" + self.directoryConfig)
        if not os.path.exists(os.getenv("HOME") + "/" + self.directoryConfig + "/" + self.fileConfig):
            with open(os.getenv("HOME") + "/" + self.directoryConfig + "/" + self.fileConfig, "w") as openfile:
                dictionary = {}
                dictionary["pathProgram"] = "None"
                json_object = json.dumps(dictionary, indent=4)
                openfile.write(json_object)
        with open(os.getenv("HOME") + "/" + self.directoryConfig + "/" + self.fileConfig, "r") as openfile:
            param = json.load(openfile)        
            print("param = ", param)
        if param["pathProgram"] != "None":
            self.programDirectory = param["pathProgram"]
            
    def saveConfiguration(self):
        """
        Saves the current configuration to a JSON file, updating the program path.

        This function loads the existing configuration from the specified JSON file, updates 
        the `pathProgram` field with the current value of `self.programDirectory`, and then 
        saves the updated configuration back to the file.

        Returns:
        None: The function does not return any value but modifies the configuration file 
        to reflect the updated program path.
        """
        print("saveConfiguration")
        with open(os.getenv("HOME") + "/" + self.directoryConfig + "/" + self.fileConfig, "r") as openfile:
            param = json.load(openfile)        
            print("param = ", param)
        print("saveConfiguration self.programDirectory = ", self.programDirectory)    
        param["pathProgram"] = self.programDirectory
        with open(os.getenv("HOME") + "/" + self.directoryConfig + "/" + self.fileConfig, "w") as openfile:
            json_object = json.dumps(param, indent=4)
            openfile.write(json_object)


    def computeNormals(self,x,y,z):
        """
        todo, not implemented
        """
        print("computeNormals")
        normal = []
        normal.append(-1)
        normal.append(-1)
        normal.append(-1)
        print("computeNormals normal = ", normal)        
        return normal
    
    def computeDirection(self,xO,yO,zO, xD,yD,zD):
        """"
        Computes the direction vector from a starting point to a destination point in 3D space.

        This function calculates the normalized direction vector between two points defined 
        by their coordinates \((xO, yO, zO)\) (origin) and \((xD, yD, zD)\) (destination). 
        It also computes the Euclidean distance between these points, which is rounded to 
        the nearest integer to determine the number of points along the direction.

        Parameters:
        xO (float): The x-coordinate of the origin point.
        yO (float): The y-coordinate of the origin point.
        zO (float): The z-coordinate of the origin point.
        xD (float): The x-coordinate of the destination point.
        yD (float): The y-coordinate of the destination point.
        zD (float): The z-coordinate of the destination point.

        Returns:
        tuple: A tuple containing:
            - vector (list): A list representing the normalized direction vector from the origin to the destination.
            - nbPoints (int): The number of points along the direction, computed as the Euclidean distance rounded to the nearest integer.
        """
        print("computeDirection")
        long = math.sqrt((xD-xO)*(xD-xO)+(yD-yO)*(yD-yO)+(zD-zO)*(zD-zO))
        vector = []
        vector.append((xD-xO)/long)
        vector.append((yD-yO)/long)
        vector.append((zD-zO)/long)
        print("computeDirection vector = ", vector)
        nbPoints =  int(long)
        return vector, nbPoints
    
       
    def computeProfile(self,x,y,z,vector,profileOutputFile):
        """"
        Computes a profile based on specified coordinates and a direction vector.

        This function runs an external program to compute a profile from a 3D dataset. 
        It takes the coordinates of a point in space, a direction vector, and various parameters 
        related to the profile computation, and executes the specified program.

        Parameters:
        x (int): The x-coordinate of the point from which to compute the profile.
        y (int): The y-coordinate of the point from which to compute the profile.
        z (int): The z-coordinate of the point from which to compute the profile.
        vector (list): A list containing the direction vector components (vx, vy, vz) for profile computation.
        profileOutputFile (str): The file path where the computed profile output will be saved.

        Returns:
        int: Returns 0 if the computation is successful, or -1 if the required program is not found.
        """
        print("computeProfile")
        if not os.path.exists(self.programDirectory + "/" + self.computeProfileProgram):
            slicer.util.warningDisplay(self.programDirectory + "/" + self.computeProfileProgram + " does not exist!\n")
            return  -1        
        print("computeProfile " + self.programDirectory + "/" + self.computeProfileProgram + " " + str(x) + " " + str(y) + " " +  str(z) + " " + str(vector[0]) +  " " + str(vector[1]) + " " + str(vector[2]) + " " + str(self.sliderStep) + " " + profileOutputFile + " " + self.inputFile + " " + str(self.sliderNeighbor) + " " + self.profileMeasurement + " " + self.profileTypeBlock)
        result = subprocess.run([self.programDirectory + "/" + self.computeProfileProgram, str(x), str(y), str(z), str(vector[0]), str(vector[1]), str(vector[2]), str(self.sliderStep), profileOutputFile, self.inputFile, str(self.sliderNeighbor), self.profileMeasurement, self.profileTypeBlock], capture_output=True, text=True)        
        print("stdout:", result.stdout)
        print("stderr:", result.stderr)
        
        self.drawProfile(profileOutputFile)
        return 0 

    def displayProfile(self, profileFile):        
        """
        Displays the profile data from the specified file.

        This method is responsible for displaying a profile by invoking the `drawProfile` method 
        with the provided profile file path. The drawing and visualization of the profile data 
        is handled internally by the `drawProfile` function.

        Args:
            profileFile (str): The file path to the profile data that needs to be displayed.

        Returns:
            int: Always returns 0 to indicate the process has been completed successfully.
        """
        print("displayProfile")        
        self.drawProfile(profileFile)
        return 0

    
    def drawProfile(self,filename):
        """
        Draws a density profile graph from a specified file and displays it in the UI.

        This method reads profile data from a text file, processes the data into a graph using `matplotlib`,
        and then displays the graph in a QLabel widget (`imageWidget`) in the UI.

        Args:
            filename (str): Path to the file containing the profile data. The file should contain lines where 
                        each line represents a set of coordinates (x, y, z) and a pixel value.        
        """
        print("drawProfile")
        try:
            import matplotlib
        except ModuleNotFoundError:
            slicer.util.pip_install("matplotlib")
            import matplotlib

        matplotlib.use("Agg")

        print("filename = ", filename)
        data = []
        with open(filename, 'r') as f:            
            for line in f:                
                l = line.split()
                x,y,z,valPixel = map(int, l[:])
                data.append((x, y, z, valPixel))


        x_abscisses = list(range(1, len(data)+1))
        valPixels = [d[3] for d in data]
        clf()
        plot(x_abscisses, valPixels, linestyle='-', marker='o')


        xlabel('(x ,y, z)')
        ylabel('valeur du pixel')
        title('Courbe du profil de densité')

        self.imageFilename = "imageProfileTemp.png"
        savefig(self.imageFilename)
        pm = qt.QPixmap(self.imageFilename)
        self.imageWidget.setPixmap(pm)
        self.imageWidget.setScaledContents(True)        
        self.imageWidget.show()


    def saveImageProfile(self,profileFile):
        """
        Saves the generated profile plot image to a file.

        This method takes the profile file as input and saves the currently displayed profile image (`imageFilename`)
        as a PNG file with the same base name as the profile file, replacing the `.txt` extension with `.png`.

        Args:
            profileFile (str): Path to the profile text file (.txt) whose name will be used to generate the output image file name.
                           If None, it defaults to using `self.profileOutputFile`.    
    
        """
        print("saveImageProfile")        
        if profileFile != None:
            outputImageProfile = profileFile.replace(".txt", ".png")
        else:
            outputImageProfile = self.profileOutputFile.replace(".txt", ".png")        
        shutil.copy(self.imageFilename, outputImageProfile)
    

    def drawProfileTest(self,filename):
        print("drawProfile")      
        '''data = np.array([5, 10, 15, 18, 20])        
        histogram = np.histogram(data, bins =5)

        chartNode = slicer.util.plot(histogram, xColumnIndex = 1)
        chartNode.SetYAxisRangeAuto(False)
        chartNode.SetYAxisRange(0, 30)'''
        '''values = np.random.uniform(5, 25, [10,2])
        chart = slicer.util.plot(values, xColumnIndex=0, columnNames=['x' ,'y'], title='My chart')'''
        '''import SampleData
        volumeNode = SampleData.downloadSample("MRHead")
        plotNodes = {}
        histogram = np.histogram(slicer.util.arrayFromVolume(volumeNode), bins=80)
        slicer.util.plot(histogram, xColumnIndex = 1, nodes = plotNodes)'''


    
    # end code Olivier
        


#
# t_ZoomRoiTest
#


class t_ZoomRoiTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """Do whatever is needed to reset the state - typically a scene clear will be enough."""
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here."""
        self.setUp()
        self.test_t_ZoomRoi1()

    def test_t_ZoomRoi1(self):
        """Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")

        # Get/create input data

        import SampleData

        registerSampleData()
        inputVolume = SampleData.downloadSample("t_ZoomRoi1")
        self.delayDisplay("Loaded test data set")

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        threshold = 100

        # Test the module logic

        logic = t_ZoomRoiLogic()

        # Test algorithm with non-inverted threshold
        logic.process(inputVolume, outputVolume, threshold, True)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], threshold)

        # Test algorithm with inverted threshold
        logic.process(inputVolume, outputVolume, threshold, False)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], inputScalarRange[1])

        self.delayDisplay("Test passed")
