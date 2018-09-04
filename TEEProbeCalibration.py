import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
from Tkinter import Tk
#
# TEEProbeCalibration
#

class TEEProbeCalibration(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "TEEProbeCalibration" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Examples"]
    self.parent.dependencies = ["VolumeResliceDriver"]
    self.parent.contributors = ["John Doe (AnyWare Corp.)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
It performs a simple thresholding on the input volume and optionally captures a screenshot.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# TEEProbeCalibrationWidget
#

class TEEProbeCalibrationWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """
  def __init__(self, parent=None):
    ScriptedLoadableModuleWidget.__init__(self, parent)
    self.customLayoutId = 85683 
    self.connectorNode = None
    self.resliceLogic = slicer.modules.volumereslicedriver.logic()
    slicer.mymod = self
    self.connectorNode = None
    self.imageNode = None
    self.OutputRegistrationTransformNode = None 
    self.sequenceNode = None 
    self.sequenceNode2 = None 
    self.sequenceBrowserNode = None 
    self.sequenceBrowserLogic = slicer.modules.sequencebrowser.logic()
    self.isVisualizing = False 
    self.connectCheck = 0 
    Tk().withdraw() 
    self.numFid = 0 
    self.ImageToProbe = vtk.vtkMatrix4x4()
    self.fiducialNode = None 
    self.logic = TEEProbeCalibrationLogic()
    self.transformNode = None
  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpRedSliceView)
    l = slicer.modules.createmodels.logic()
    self.needleModel = l.CreateNeedle(150, 0.4, 0, False)
    #This code block creates a collapsible button 
    #This defines which type of button you are using 
    self.usContainer = ctk.ctkCollapsibleButton()
    #This is what the button will say 
    self.usContainer.text = "Connection Information"
    #Thiss actually creates that button
    #This creates a variable that describes layout within this collapsible button 
    self.usLayout = qt.QFormLayout(self.usContainer)

    if slicer.mrmlScene.GetNodesByClass("vtkMRMLSequenceNode").GetNumberOfItems() == 0:
      #This is a push button 
      self.connectButton = qt.QPushButton()
      self.connectButton.setDefault(False)
      #This button says connect 
      self.connectButton.text = "Connect"
      #help tooltip that explains the funciton 
      self.connectButton.toolTip = "Connects to Ultrasound"
      #adds the widget to the layout 
      self.usLayout.addWidget(self.connectButton)
    
    # self.normalImageButton = qt.QCheckBox() 
    # self.normalImageButton.text = "Select if performing a 2D Calibration"
    # self.usLayout.addRow(self.normalImageButton)
    
    self.imageSelector = slicer.qMRMLNodeComboBox()
    self.imageSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.imageSelector.selectNodeUponCreation = True
    self.imageSelector.addEnabled = False
    self.imageSelector.removeEnabled = False
    self.imageSelector.noneEnabled = True
    self.imageSelector.showHidden = False
    self.imageSelector.showChildNodeTypes = False
    self.imageSelector.setMRMLScene( slicer.mrmlScene )
    self.imageSelector.setToolTip( "Pick the image to be used." )
    self.usLayout.addRow("US Volume: ", self.imageSelector)
    
        #add combo box for linear transform node 
    self.TransformSelector = slicer.qMRMLNodeComboBox()
    self.TransformSelector.nodeTypes = ["vtkMRMLLinearTransformNode"]
    self.TransformSelector.selectNodeUponCreation = True
    self.TransformSelector.addEnabled = False
    self.TransformSelector.removeEnabled = False
    self.TransformSelector.noneEnabled = True
    self.TransformSelector.showHidden = False
    self.TransformSelector.showChildNodeTypes = False
    self.TransformSelector.setMRMLScene( slicer.mrmlScene )
    self.TransformSelector.setToolTip( "Pick the transform representing the straw line." )
    self.usLayout.addRow("Tip to Probe: ", self.TransformSelector)
    
    self.recordContainer = ctk.ctkCollapsibleButton()
    #This is what the button will say 
    self.recordContainer.text = "Recording Options"
    #Thiss actually creates that button
    #This creates a variable that describes layout within this collapsible button 
    self.recordLayout = qt.QFormLayout(self.recordContainer)
    
    self.RecordButton = qt.QPushButton() 
    self.RecordButton.text = "Start Recording" 
    self.recordLayout.addWidget(self.RecordButton)
    
    self.StopRecordButton = qt.QPushButton() 
    self.StopRecordButton.text = "Stop Recording" 
    self.recordLayout.addWidget(self.StopRecordButton)
    
    self.pathInput = qt.QLineEdit()
    self.pathInput.setPlaceholderText("Enter the path to save files to")
    self.pathText = qt.QLabel("File Path:")
    self.recordLayout.addRow(self.pathText, self.pathInput)
    
    self.SaveRecordButton = qt.QPushButton() 
    self.SaveRecordButton.text = "Save Recording" 
    self.recordLayout.addWidget(self.SaveRecordButton)
    
     # This creates another collapsible button
    self.fiducialContainer = ctk.ctkCollapsibleButton()
    self.fiducialContainer.text = "Registration"

    self.fiducialLayout = qt.QFormLayout(self.fiducialContainer)

    self.freezeButton = qt.QPushButton()
    if slicer.mrmlScene.GetNodesByClass("vtkMRMLSequenceNode").GetNumberOfItems() == 0:
      self.freezeButton.text = "Freeze"
    else:
      self.freezeButton.text = "Place Fiducial"
    self.freezeButton.toolTip = "Freeze the ultrasound image for fiducial placement"
    self.fiducialLayout.addRow(self.freezeButton)
    self.shortcut = qt.QShortcut(qt.QKeySequence('f'), slicer.util.mainWindow())
    
    self.numFidLabel = qt.QLabel()
    self.fiducialLayout.addRow(qt.QLabel("Fiducials collected:"), self.numFidLabel)

    self.transformTable = qt.QTableWidget() 
    self.transTableItem = qt.QTableWidgetItem()
    self.fidError = qt.QLabel()
    self.transformTable.setRowCount(4)
    self.transformTable.setColumnCount(4)
    self.transformTable.horizontalHeader().hide()
    self.transformTable.verticalHeader().hide()
    self.transformTable.setItem(0,0, qt.QTableWidgetItem("1"))
    self.transformTable.setItem(0,1, qt.QTableWidgetItem("0"))
    self.transformTable.setItem(0,2, qt.QTableWidgetItem("0"))
    self.transformTable.setItem(0,3, qt.QTableWidgetItem("0"))
    self.transformTable.setItem(1,0, qt.QTableWidgetItem("0"))
    self.transformTable.setItem(1,1, qt.QTableWidgetItem("1"))
    self.transformTable.setItem(1,2, qt.QTableWidgetItem("0"))
    self.transformTable.setItem(1,3, qt.QTableWidgetItem("0"))
    self.transformTable.setItem(2,0, qt.QTableWidgetItem("0"))
    self.transformTable.setItem(2,1, qt.QTableWidgetItem("0"))
    self.transformTable.setItem(2,2, qt.QTableWidgetItem("1"))
    self.transformTable.setItem(2,3, qt.QTableWidgetItem("0"))
    self.transformTable.setItem(3,0, qt.QTableWidgetItem("0"))
    self.transformTable.setItem(3,1, qt.QTableWidgetItem("0"))
    self.transformTable.setItem(3,2, qt.QTableWidgetItem("0"))
    self.transformTable.setItem(3,3, qt.QTableWidgetItem("1"))
    self.transformTable.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.MinimumExpanding)
    self.copyIcon =qt.QIcon(":Icons/Medium/SlicerEditCopy.png")
    self.copyButton = qt.QPushButton()
    self.copyButton.setIcon(self.copyIcon)
    self.copyButton.setMaximumWidth(64)
    self.copyButton.enabled = False 
    if self.numFidLabel >= 2: 
      self.copyButton.enabled = True 
      
    self.fiducialLayout.addRow(qt.QLabel("Image to probe transform:"))
    self.fiducialLayout.addRow(self.transformTable)
    self.fiducialLayout.addRow("Copy:", self.copyButton)
    
    self.validationContainer = ctk.ctkCollapsibleButton()
    self.validationContainer.text = "Validation"
    self.validationLayout = qt.QFormLayout(self.validationContainer)

    self.visualizeButton = qt.QPushButton('Show 3D Scene')
    self.visualizeButton.toolTip = "This button enables the 3D view for visual validation"
    self.validationLayout.addRow(self.visualizeButton)
    
    # Add the containers to the parent
    self.layout.addWidget(self.usContainer)
    if slicer.mrmlScene.GetNodesByClass("vtkMRMLSequenceNode").GetNumberOfItems() == 0:
      self.layout.addWidget(self.recordContainer)
    self.layout.addWidget(self.fiducialContainer)
    self.layout.addWidget(self.validationContainer)
    
    # Add vertical spacer
    self.layout.addStretch(1)
    
    #connections
    if slicer.mrmlScene.GetNodesByClass("vtkMRMLSequenceNode").GetNumberOfItems() == 0:
      self.connectButton.connect('clicked(bool)', self.onConnectButtonClicked)
      self.freezeButton.connect('clicked(bool)', self.onConnectButtonClicked)
      self.shortcut.connect('activated()', self.onConnectButtonClicked)
    else:
      self.shortcut.connect('activated()', self.onFiducialClicked)
      self.freezeButton.connect('clicked(bool)', self.onFiducialClicked)
    self.imageSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onImageChanged)
    self.TransformSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onTransformChanged)
    self.RecordButton.connect('clicked(bool)', self.onRecordButtonClicked)
    self.StopRecordButton.connect('clicked(bool)', self.onStopRecordButtonClicked)
    self.SaveRecordButton.connect('clicked(bool)', self.onSaveRecordButtonClicked)
    self.copyButton.connect('clicked(bool)', self.onCopyButtonClicked)
    self.visualizeButton.connect('clicked(bool)', self.onVisualizeButtonClicked)

    self.StopRecordButton.setEnabled(False)
    self.sceneObserverTag = slicer.mrmlScene.AddObserver(slicer.mrmlScene.NodeAddedEvent, self.onNodeAdded)
    
  @vtk.calldata_type(vtk.VTK_OBJECT)
  def onNodeAdded(self, caller, event, callData):
    # if the node that is created is of type vtkMRMLMarkupsFiducialNODE 
    if type(callData) is slicer.vtkMRMLMarkupsFiducialNode:
      # if there is something in this node 
      if self.fiducialNode is not None:
        # remove the observer
        self.fiducialNode.RemoveAllMarkups()
        self.fiducialNode.RemoveObserver(self.markupAddedObserverTag) 

      self.fiducialNode = callData
      #sets a markupObserver to notice when a markup gets added
      self.markupAddedObserverTag = self.fiducialNode.AddObserver(slicer.vtkMRMLMarkupsNode.MarkupAddedEvent, self.onMarkupAdded)
      #this runs the function onMarkupAdded
      self.onMarkupAdded(self.fiducialNode, slicer.vtkMRMLMarkupsNode.MarkupAddedEvent)
    if type(callData) is slicer.vtkMRMLSequenceBrowserNode:
      if self.connectorNode is None: 
        self.onSequenceAdded()
        self.connectCheck = 1

  def onMarkupAdded(self, fiducialNodeCaller, event):
    # Set the location and index to zero because its needs to be initialized
    centroid=[0,0,0]
    # This checks if there is not a display node 
    if self.fiducialNode.GetDisplayNode() is None:
      # then creates one if that is the case 
      self.fiducialNode.CreateDefaultDisplayNodes()
    # This sets a variable as the display node
    displayNode = self.fiducialNode.GetDisplayNode()
    # This sets the type to be a cross hair
    displayNode.SetGlyphType(3)
    # This sets the size
    displayNode.SetGlyphScale(2.5)
    # This says that you dont want text
    displayNode.SetTextScale(0)
    # This sets the color
    displayNode.SetSelectedColor(0, 0, 1)
    # This saves the location the markup is place
    # Collect the point in image space
    self.fiducialNode.GetMarkupPoint(self.fiducialNode.GetNumberOfMarkups()-1, 0, centroid)
    tipToProbeTransform = vtk.vtkMatrix4x4()
    self.TransformSelector.currentNode().GetMatrixTransformToWorld(tipToProbeTransform)
    origin = [tipToProbeTransform.GetElement(0, 3), tipToProbeTransform.GetElement(1,3), tipToProbeTransform.GetElement(2,3)]
    dir = [tipToProbeTransform.GetElement(0, 2), tipToProbeTransform.GetElement(1,2), tipToProbeTransform.GetElement(2,2)]
    self.logic.AddPointAndLineMan([centroid[0],centroid[1],0], origin, dir)
    self.ImageToProbe = self.logic.manualRegLogic.CalculateRegistration()
    self.transformTable.setItem(0,0, qt.QTableWidgetItem(str(self.ImageToProbe.GetElement(0,0))))
    self.transformTable.setItem(0,1, qt.QTableWidgetItem(str(self.ImageToProbe.GetElement(0,1))))
    self.transformTable.setItem(0,2, qt.QTableWidgetItem(str(self.ImageToProbe.GetElement(0,2))))
    self.transformTable.setItem(0,3, qt.QTableWidgetItem(str(self.ImageToProbe.GetElement(0,3))))
    self.transformTable.setItem(1,0, qt.QTableWidgetItem(str(self.ImageToProbe.GetElement(1,0))))
    self.transformTable.setItem(1,1, qt.QTableWidgetItem(str(self.ImageToProbe.GetElement(1,1))))
    self.transformTable.setItem(1,2, qt.QTableWidgetItem(str(self.ImageToProbe.GetElement(1,2))))
    self.transformTable.setItem(1,3, qt.QTableWidgetItem(str(self.ImageToProbe.GetElement(1,3))))
    self.transformTable.setItem(2,0, qt.QTableWidgetItem(str(self.ImageToProbe.GetElement(2,0))))
    self.transformTable.setItem(2,1, qt.QTableWidgetItem(str(self.ImageToProbe.GetElement(2,1))))
    self.transformTable.setItem(2,2, qt.QTableWidgetItem(str(self.ImageToProbe.GetElement(2,2))))
    self.transformTable.setItem(2,3, qt.QTableWidgetItem(str(self.ImageToProbe.GetElement(2,3))))
    self.transformTable.setItem(3,0, qt.QTableWidgetItem(str(self.ImageToProbe.GetElement(3,0))))
    self.transformTable.setItem(3,1, qt.QTableWidgetItem(str(self.ImageToProbe.GetElement(3,1))))
    self.transformTable.setItem(3,2, qt.QTableWidgetItem(str(self.ImageToProbe.GetElement(3,2))))
    self.transformTable.setItem(3,3, qt.QTableWidgetItem(str(self.ImageToProbe.GetElement(3,3))))
    self.transformTable.resizeColumnToContents(0)
    self.transformTable.resizeColumnToContents(1)
    self.transformTable.resizeColumnToContents(2)
    self.transformTable.resizeColumnToContents(3)
    slicer.app.layoutManager().sliceWidget("Red").sliceController().fitSliceToBackground()
    
    if slicer.mrmlScene.GetNodesByClass("vtkMRMLSequenceNode").GetNumberOfItems() == 0:  
      self.connectorNode.Start()
      self.connectButton.text = "Disconnect"
      self.freezeButton.text = "Freeze"

  def onConnectButtonClicked(self):
    if self.connectorNode is None: 
      if self.connectCheck == 1: 
        if self.imageNode or self.transformNode is None: 
          if self.imageSelector.currentNode() is None: 
            print('Please select an US volume')
          if self.TransformSelector.currentNode() is None:
            print('Please select the tip to probe transform')
        if self.imageNode and self.transformNode is not None:
          if self.fiducialNode is not None: 
            self.fiducialNode.RemoveAllMarkups()
          self.numFid = self.numFid+1 
          self.numFidLabel.setText(str(self.numFid))
          self.OutputRegistrationTransformNode = slicer.vtkMRMLLinearTransformNode()
          slicer.mrmlScene.AddNode(self.OutputRegistrationTransformNode) 
          self.OutputRegistrationTransformNode.SetName('ImageToProbe') 
          slicer.modules.markups.logic().StartPlaceMode(0)
          slicer.app.layoutManager().sliceWidget('Red').setCursor(qt.QCursor(2))
      else:
        self.connectorNode = slicer.vtkMRMLIGTLConnectorNode()
        # Adds this node to the scene, not there is no need for self here as it is its own node
        slicer.mrmlScene.AddNode(self.connectorNode)
        # Configures the connector
        self.connectorNode.SetTypeClient('localhost', 18944)
        self.connectorNode.Start()
    else:
      if self.connectorNode.GetState() == 2:
          self.connectorNode.Stop()
          self.connectButton.text = "Connect"
          self.freezeButton.text = "Unfreeze"
          self.numFid = self.numFid + 1 
          self.numFidLabel.setText(str(self.numFid))
          self.OutputRegistrationTransformNode = slicer.vtkMRMLLinearTransformNode()
          slicer.mrmlScene.AddNode(self.OutputRegistrationTransformNode) 
          self.OutputRegistrationTransformNode.SetName('ImageToProbe') 
          slicer.modules.markups.logic().StartPlaceMode(0)
          slicer.app.layoutManager().sliceWidget('Red').setCursor(qt.QCursor(2))
      else:
          # This starts the connection
          self.connectorNode.Start()
          self.connectButton.text = "Disconnect"
          self.freezeButton.text = "Freeze"
      if self.fiducialNode is not None:
        self.fiducialNode.RemoveAllMarkups()

  def onImageChanged(self):
    if self.imageNode is not None:
      # Unparent
      self.imageNode.SetAndObserveTransformNodeID(None)
      self.imageNode = None
      self.imageNode = self.imageSelector.currentNode() 
      if self.imageNode is None: 
        print('Please select an US volume')
      if self.imageNode is not None: 
        self.imageNode.GetDisplayNode().SetAutoWindowLevel(0)
        self.imageNode.GetDisplayNode().SetWindowLevelMinMax(0,120)
        slicer.app.layoutManager().sliceWidget('Red').sliceLogic().GetSliceCompositeNode().SetBackgroundVolumeID(self.imageSelector.currentNode().GetID())
        # Configure volume reslice driver, transverse
        self.resliceLogic.SetDriverForSlice(self.imageSelector.currentNode().GetID(), slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed'))
        self.resliceLogic.SetModeForSlice(self.resliceLogic.MODE_TRANSVERSE, slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed'))
        slicer.app.layoutManager().sliceWidget("Red").sliceController().fitSliceToBackground()
        if biplaneButton.isChecked() == True: 
          self.ROInode = slicer.vtkMRMLAnnotationROINode()
          self.ROInode.setName("LeftROI")
          slicer.mrmlScene.addNode(self.ROInode)
    else:  
      self.imageNode = self.imageSelector.currentNode()
      self.imageNode.GetDisplayNode().SetAutoWindowLevel(0)
      self.imageNode.GetDisplayNode().SetWindowLevelMinMax(0,120)
      slicer.app.layoutManager().sliceWidget('Red').sliceLogic().GetSliceCompositeNode().SetBackgroundVolumeID(self.imageSelector.currentNode().GetID())
      # Configure volume reslice driver, transverse
      self.resliceLogic.SetDriverForSlice(self.imageSelector.currentNode().GetID(), slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed'))
      self.resliceLogic.SetModeForSlice(self.resliceLogic.MODE_TRANSVERSE, slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed'))
      slicer.app.layoutManager().sliceWidget("Red").sliceController().fitSliceToBackground()

  def onTransformChanged(self):
    if self.transformNode is not None: 
      self.transformNode.SetAndObserveTransformNodeID(None) 
      self.transformNode = None 
    self.transformNode = self.TransformSelector.currentNode()
    if self.transformNode is None:
      print('Please select a tip to probe transform')
    else:
      self.needleModel.SetAndObserveTransformNodeID(self.TransformSelector.currentNode().GetID()) 

  def onVisualizeButtonClicked(self):
    if self.fiducialNode is not None:
      self.fiducialNode.RemoveAllMarkups()
    if self.isVisualizing:
      slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpRedSliceView)    
      self.isVisualizing = False
      self.visualizeButton.text = 'Show 3D Scene'
      self.OutputRegistrationTransformNode.SetMatrixTransformToParent(None)
    else:
      self.isVisualizing = True
      slicer.app.layoutManager().sliceWidget('Red').sliceLogic().GetSliceNode().SetSliceVisible(True)
      slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUp3DView)
      self.visualizeButton.text = 'Show ultrasound stream'
      if self.imageNode or self.transformNode is None: 
        if self.imageNode is None:
          print('Please select an US volume')
        if self.transformNode is None:
          print('Please select a tip to probe transform')
      if self.imageNode and self.transformNode is not None:
        self.imageNode.SetAndObserveTransformNodeID(self.OutputRegistrationTransformNode.GetID())
        self.OutputRegistrationTransformNode.SetMatrixTransformToParent(self.ImageToProbe)

  def onRecordButtonClicked(self):
    if self.connectCheck == 0:
      if self.sequenceBrowserNode is None:
        if self.imageSelector.currentNode is None: 
          print('Please select an US volume')
        else:
          slicer.modules.sequencebrowser.setToolBarVisible(1)
          self.sequenceBrowserNode =slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSequenceBrowserNode")
          self.sequenceBrowserNode.SetName( slicer.mrmlScene.GetUniqueNameByString( "Recording" ))
          self.sequenceBrowserNode.SetAttribute("Recorded", "True")
          self.sequenceBrowserNode.SetScene(slicer.mrmlScene)
          slicer.mrmlScene.AddNode(self.sequenceBrowserNode)
          self.sequenceBrowserLogic = slicer.modules.sequencebrowser.logic()
          self.modifyFlag = self.sequenceBrowserNode.StartModify()
          self.sequenceNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSequenceNode")
          self.sequenceNode2 = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSequenceNode")
          self.sequenceBrowserNode.AddProxyNode(self.TransformSelector.currentNode(), self.sequenceNode)
          self.sequenceBrowserNode.AddProxyNode(self.imageSelector.currentNode(), self.sequenceNode2)
          self.sequenceBrowserLogic.AddSynchronizedNode(self.sequenceNode, self.TransformSelector.currentNode(), self.sequenceBrowserNode)
          self.sequenceBrowserLogic.AddSynchronizedNode(self.sequenceNode2, self.imageSelector.currentNode(), self.sequenceBrowserNode)
          self.sequenceBrowserNode.EndModify(self.modifyFlag)
          self.RecordButton.text = "Recording"
          self.StopRecordButton.setEnabled(True)
          # self.sequenceBrowserNode.SetRecording(self.sequenceNode, self.sequenceNode2, True)
          # TRYING THIS SEEING IF IT WORKS! 
          self.sequenceBrowserNode.SetRecording(self.sequenceNode, True)
          self.sequenceBrowserNode.SetRecording(self.sequenceNode2, True)
          self.sequenceBrowserNode.SetRecordingActive(True)
      else:
        if self.sequenceBrowserNode.GetRecordingActive() == True:
          # self.sequenceBrowserNode.SetRecording(self.sequenceNode, self.sequenceNode2, True)
          self.sequenceBrowserNode.SetRecording(self.sequenceNode, True)
          self.sequenceBrowserNode.SetRecording(self.sequenceNode2, True)
          # self.sequenceBrowserNode.SetRecordingActive(True)
        else: 
          print('The Sequence is currently recording')

  def onFiducialClicked(self):
    if self.fiducialNode is not None: 
      self.fiducialNode.RemoveAllMarkups()
    self.numFid = self.numFid + 1 
    self.numFidLabel.setText(str(self.numFid))
    self.OutputRegistrationTransformNode = slicer.vtkMRMLLinearTransformNode()
    slicer.mrmlScene.AddNode(self.OutputRegistrationTransformNode) 
    self.OutputRegistrationTransformNode.SetName('ImageToProbe') 
    slicer.modules.markups.logic().StartPlaceMode(0)
    slicer.app.layoutManager().sliceWidget('Red').setCursor(qt.QCursor(2))

  
  def onStopRecordButtonClicked(self): 
    if self.sequenceBrowserNode is not None: 
      if self.sequenceBrowserNode.GetRecordingActive() == True:
        self.RecordButton.text = "Start Recording"
        self.sequenceBrowserNode.SetRecording(self.sequenceNode, False)
        self.sequenceBrowserNode.SetRecording(self.sequenceNode2,False)
        self.sequenceBrowserNode.SetRecordingActive(False)
        self.StopRecordButton.enabled = False 

  def onSaveRecordButtonClicked(self):
    if self.pathInput.text is None: 
      print('Please enter the file path')
    else:
      print('Files saved')
      self.filePath = str(self.pathInput.text)
      slicer.util.saveScene(self.filePath+'/SlicerSceneUSCalibration.mrml')
      slicer.util.saveNode(self.imageSelector.currentNode(), str(self.pathInput.text)+'/Image_Probe.nrrd')
      slicer.util.saveNode(self.TransformSelector.currentNode(),str(self.pathInput.text)+'/NeedleTipToProbe.h5')
      slicer.util.saveNode(self.sequenceNode, str(self.pathInput.text)+'/Sequence.seq.mha')
      slicer.util.saveNode(self.sequenceNode2, str(self.pathInput.text)+'/Sequence_1.seq.nrrd')

  def onCopyButtonClicked(self,numFidLabel):
    if self.numFidLabel >=1:
      self.outputTransform = '[' + str(self.ImageToProbe.GetElement(0,0))+','+ str(self.ImageToProbe.GetElement(0,1))+','+str(self.ImageToProbe.GetElement(0,2))+';'+str(self.ImageToProbe.GetElement(1,0))+','+str(self.ImageToProbe.GetElement(1,1))+','+str(self.ImageToProbe.GetElement(1,2))+';'+str(self.ImageToProbe.GetElement(2,0))+','+str(self.ImageToProbe.GetElement(2,1))+','+str(self.ImageToProbe.GetElement(0,0))+']'
    else:
      self.outputTransform = 'Calibration Required' 
    root = Tk()
    root.overrideredirect(1)
    root.withdraw()
    root.clipboard_clear() 
    root.clipboard_append(self.outputTransform)
    root.update()
    root.destroy()
    
  def onSequenceAdded(self):
    self.connectButton.setText("")
    self.usLayout.removeWidget(self.connectButton)
    self.RecordButton.setText("")
    self.recordLayout.removeWidget(self.RecordButton) 
    self.StopRecordButton.setText("")
    self.recordLayout.removeWidget(self.StopRecordButton)
    self.pathText.setText("")
    self.recordLayout.removeWidget(self.pathText)
    self.pathInput.placeholderText = ""
    self.recordLayout.removeWidget(self.pathInput)
    self.SaveRecordButton.setText("")
    self.recordLayout.removeWidget(self.SaveRecordButton)
    self.recordContainer.collapsed = True 
    
    self.freezeButton.enabled = True 
    self.freezeButton.text = "Place fiducial"
    self.connectButton.enabled = True 
  def cleanup(self):
    pass


class TEEProbeCalibrationLogic(ScriptedLoadableModuleLogic):
  def __init__(self):
    self.manualRegLogic = slicer.vtkSlicerPointToLineRegistrationLogic()
    self.autoRegLogic = slicer.vtkSlicerPointToLineRegistrationLogic()
    self.manualRegLogic.SetLandmarkRegistrationModeToSimilarity()
    self.autoRegLogic.SetLandmarkRegistrationModeToSimilarity()

  def AddPointAndLineMan(self, point, lineOrigin, lineDirection):
    self.manualRegLogic.AddPointAndLine(point, lineOrigin, lineDirection)
  
  def AddPointAndLineAuto(self, point, lineOrigin, lineDirection):
    self.autoRegLogic.AddPointAndLine(point, lineOrigin, lineDirection)