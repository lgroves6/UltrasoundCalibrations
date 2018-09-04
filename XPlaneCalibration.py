import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
from Tkinter import Tk 
#
# XPlaneCalibration
#

class XPlaneCalibration(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "XPlaneCalibration" # TODO make this more human readable by adding spaces
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
# XPlaneCalibrationWidget
#

class XPlaneCalibrationWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """
  def __init__(self, parent = None):
    ScriptedLoadableModuleWidget.__init__(self, parent)
    self.resliceLogic = slicer.modules.volumereslicedriver.logic()
    self.sequenceBrowserLogic = slicer.modules.sequencebrowser.logic()
    Tk().withdraw()
    self.numFid = 0 
    self.ImageToProbe = vtk.vtkMatrix4x4()
    self.leftMat = vtk.vtkMatrix4x4()
    self.rightMat = vtk.vtkMatrix4x4()
    self.ImageToProbeMat = vtk.vtkMatrix4x4()
    self.leftTransform = vtk.vtkTransform()
    self.rightTransform = vtk.vtkTransform()
    self.fiducialNode = None 
    self.logic = XPlaneCalibrationLogic()
    self.transformNode = None
    slicer.mymod = self 
    self.connectorNode = None
    self.connectorNode2 = None 
    self.imageNode = None
    self.imageNode2 = None
    self.fidCount = 1
    self.connectCheck = 0
    self.isVisualizing = False
    self.sequenceBrowserNode = None 
    self.sequenceBrowserLogic = slicer.modules.sequencebrowser.logic()
    self.sequenceNode = None 
    self.sequenceNode2 = None 
    self.sequenceNode3 = None
    self.cropping = 0 
    clipOutsideSurface = True 

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    # layoutLogic = slicer.app.layoutManager.layoutLogic()
    slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutSideBySideView)    
    l = slicer.modules.createmodels.logic()
    self.needleModel = l.CreateNeedle(150, 0.4, 0, False)
    self.redWidget = slicer.app.layoutManager().sliceWidget('Red')
    self.yellowWidget = slicer.app.layoutManager().sliceWidget('Yellow')    
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
      self.connectButton.toolTip = "Connects to ultrasound"
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
    self.usLayout.addRow("Left view volume: ", self.imageSelector)
    
    
    self.imageSelector2 = slicer.qMRMLNodeComboBox()
    self.imageSelector2.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.imageSelector2.selectNodeUponCreation = True
    self.imageSelector2.addEnabled = False
    self.imageSelector2.removeEnabled = False
    self.imageSelector2.noneEnabled = True
    self.imageSelector2.showHidden = False
    self.imageSelector2.showChildNodeTypes = False
    self.imageSelector2.setMRMLScene( slicer.mrmlScene )
    self.imageSelector2.setToolTip( "Pick the image to be used." )
    self.usLayout.addRow("Right view volume: ", self.imageSelector2)
    
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
    self.visualizeButton.connect('clicked(bool)', self.onVisualizeButtonClicked)
    
    self.layout.addWidget(self.usContainer)
    if slicer.mrmlScene.GetNodesByClass("vtkMRMLSequenceNode").GetNumberOfItems() == 0:
      self.layout.addWidget(self.recordContainer)
    self.layout.addWidget(self.fiducialContainer)
    self.layout.addWidget(self.validationContainer)
    
    if slicer.mrmlScene.GetNodesByClass("vtkMRMLSequenceNode").GetNumberOfItems() == 0:
      self.connectButton.connect('clicked(bool)', self.onConnectButtonClicked)
      self.freezeButton.connect('clicked(bool)', self.onConnectButtonClicked)
      self.shortcut.connect('activated()', self.onConnectButtonClicked)
      self.RecordButton.connect('clicked(bool)', self.onRecordButtonClicked)
      self.StopRecordButton.connect('clicked(bool)', self.onStopButtonClicked)
      self.SaveRecordButton.connect('clicked(bool)', self.onSaveButtonClicked)
    else: 
      self.shortcut.connect('activated()', self.onFiducialClicked)
      self.freezeButton.connect('clicked(bool)', self.onFiducialClicked)
    self.imageSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onImageChanged)
    self.imageSelector2.connect('currentNodeChanged(vtkMRMLNode*)', self.onImageChanged2)
    self.TransformSelector.connect('currentNodeChanged(vtkMRMLNode*)',self.onTransformChanged)
    self.copyButton.connect('clicked(bool)', self.onCopyButtonClicked)
    
    self.layout.addStretch(1)
  
    self.sceneObserverTag = slicer.mrmlScene.AddObserver(slicer.mrmlScene.NodeAddedEvent, self.onNodeAdded)
  @vtk.calldata_type(vtk.VTK_OBJECT)
  def onNodeAdded(self, caller, event, callData):
    # if the node that is created is of type vtkMRMLMarkupsFiducialNODE 
    if type(callData) is slicer.vtkMRMLMarkupsFiducialNode:
      if self.cropping == 0:
        if self.fidCount == 1: 
          self.fidCount = 0 
        else:
          self.fidCount = 1
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
      if self.cropping == 1: 
        return
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
    if self.fidCount == 0:
      self.logic.AddPointAndLineMan([centroid[0],centroid[1],0], origin, dir)
    if self.fidCount == 1: 
      self.logic.AddPointAndLineMan([0,centroid[1],centroid[2]], origin, dir)
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
    self.fiducialNode.RemoveAllMarkups()
    self.fiducialNode.RemoveObserver(self.markupAddedObserverTag) 
    slicer.mrmlScene.RemoveNode(self.fiducialNode)
    self.fiducialNode = None
    if slicer.mrmlScene.GetNodesByClass("vtkMRMLSequenceNode").GetNumberOfItems() == 0:
      if self.fidCount == 0: 
        slicer.modules.markups.logic().StartPlaceMode(0)
        self.redWidget.setCursor(qt.QCursor(2))
        self.yellowWidget.setCursor(qt.QCursor(2))
      if self.fidCount == 1:
        self.connectorNode.Start()
        self.connectorNode2.Start()
        self.connectButton.text = "Disconnect"
        self.freezeButton.text = "Freeze"
      
  def onConnectButtonClicked(self): 
    if self.connectorNode is None:
      if self.connectCheck == 1: 
        if self.imageNode or self.imageNode2 or self.transformNode is None: 
          if self.imageNode is None: 
            print('Please select an US volume')
          if self.transformNode is None:
            print('Please select the tip to probe transform')
          if self.imageNode2 is None: 
            print('Please select the right volume')
        if self.imageNode and self.imageNode2 and self.transformNode is not None:
          if self.fiducialNode is not None: 
              self.fiducialNode.RemoveAllMarkups()
          self.numFid = self.numFid +1
          self.numFidLabel.setText(str(self.numFid))
          slicer.modules.markups.logic().StartPlaceMode(0)
          self.redWidget.setCursor(qt.QCursor(2))
          self.yellowWidget.setCursor(qt.QCursor(2))
      else:
        self.connectorNode = slicer.vtkMRMLIGTLConnectorNode()
        slicer.mrmlScene.AddNode(self.connectorNode) 
        self.connectorNode.SetTypeClient('localhost', 18944)
        self.connectorNode2 = slicer.vtkMRMLIGTLConnectorNode()
        slicer.mrmlScene.AddNode(self.connectorNode2)
        self.connectorNode2.SetTypeClient('localhost',18945)
        self.connectorNode.Start() 
        self.connectorNode2.Start()
    else: 
      if self.connectorNode.GetState() == 2: 
        self.connectorNode.Stop()
        self.connectorNode2.Stop()
        self.connectButton.text = "Connect"
        self.freezeButton.text = "Unfreeze"
        self.numFid = self.numFid + 1
        self.numFidLabel.setText(str(self.numFid))
        slicer.modules.markups.logic().StartPlaceMode(0)
        self.redWidget.setCursor(qt.QCursor(2))
        self.yellowWidget.setCursor(qt.QCursor(2))
      else: 
        self.connectorNode.Start() 
        self.connectButton.text = "Disconnect"
        self.freezeButton.text = "Freeze"
      if self.fiducialNode is not None: 
        self.fiducialNode.RemoveAllMarkups() 

  def onImageChanged(self):
    self.InputRegistrationTransformNode = slicer.vtkMRMLLinearTransformNode() 
    slicer.mrmlScene.AddNode(self.InputRegistrationTransformNode)
    if self.imageNode is not None: 
      self.imageNode.SetAndObserveTransformNodeID(None) 
      self.imageNode = None 
      self.imageNode = self.imageSelector.currentNode()
      if self.imageNode is None: 
        print('Please select the left volume')
      if self.imageNode is not None:
        self.cropping = 1 
        self.imageNode = self.imageSelector.currentNode()
        self.clippingModel = slicer.vtkMRMLModelNode()
        self.clippingModel.SetName('Clipping Model')
        slicer.mrmlScene.AddNode(self.clippingModel)
        self.displayNode = slicer.vtkMRMLMarkupsDisplayNode()
        slicer.mrmlScene.AddNode(self.displayNode)
        self.inputMarkup = slicer.vtkMRMLMarkupsFiducialNode()
        self.inputMarkup.SetName('C')
        slicer.mrmlScene.AddNode(self.inputMarkup)
        self.inputMarkup.SetAndObserveDisplayNodeID(self.displayNode.GetID())
        self.inputMarkup.AddFiducial(234,509,-0.5)
        self.inputMarkup.AddFiducial(234,509,0.0)
        self.inputMarkup.AddFiducial(500,130,0)
        self.inputMarkup.AddFiducial(242,36,0)
        self.inputMarkup.AddFiducial(-26,162,0)
        self.inputMarkup.SetDisplayVisibility(0)
        self.outputVolume = slicer.vtkMRMLScalarVolumeNode()
        slicer.mrmlScene.AddNode(self.outputVolume) 
        self.logic.updateModelFromMarkup(self.inputMarkup,self.clippingModel)
        self.logic.clipVolumeWithModel(self.imageNode, self.clippingModel, True, 255, self.outputVolume)
        self.logic.showInSliceViewers(self.outputVolume, ["Red"])
        self.cropping == 0 
        self.leftMat.SetElement(0,3,-230)
        self.leftMat.SetElement(1,1,-1)
        self.leftMat.SetElement(1,3,520)
        self.leftMat.SetElement(2,2,-1)
        self.leftTransform.PostMultiply()
        self.leftTransform.Identity()  
        self.leftTransform.Concatenate(self.leftMat)  
        self.outputVolume.GetDisplayNode().SetAutoWindowLevel(0)
        self.outputVolume.GetDisplayNode().SetWindowLevelMinMax(25,100)
        self.redWidget.sliceLogic().GetSliceCompositeNode().SetBackgroundVolumeID(self.outputVolume.GetID())
        self.resliceLogic.SetDriverForSlice(self.outputVolume.GetID(), slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed'))
        self.resliceLogic.SetModeForSlice(self.resliceLogic.MODE_TRANSVERSE, slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed'))
        self.clippingModel.SetDisplayVisibility(False)
        slicer.app.layoutManager().sliceWidget('Red').sliceLogic().GetSliceNode().SetSliceVisible(True)
        slicer.app.layoutManager().sliceWidget("Red").sliceController().fitSliceToBackground()
        self.outputVolume.SetAndObserveTransformNodeID(self.InputRegistrationTransformNode.GetID())
        self.InputRegistrationTransformNode.SetMatrixTransformToParent(self.leftTransform.GetMatrix())
    if self.imageNode is None:
      self.cropping = 1 
      self.imageNode = self.imageSelector.currentNode()
      self.clippingModel = slicer.vtkMRMLModelNode()
      self.clippingModel.SetName('Clipping Model')
      slicer.mrmlScene.AddNode(self.clippingModel)
      self.displayNode = slicer.vtkMRMLMarkupsDisplayNode()
      slicer.mrmlScene.AddNode(self.displayNode)
      self.inputMarkup = slicer.vtkMRMLMarkupsFiducialNode()
      self.inputMarkup.SetName('C')
      slicer.mrmlScene.AddNode(self.inputMarkup)
      self.inputMarkup.SetAndObserveDisplayNodeID(self.displayNode.GetID())
      self.inputMarkup.AddFiducial(234,509,-0.5)
      self.inputMarkup.AddFiducial(234,509,0.0)
      self.inputMarkup.AddFiducial(500,130,0)
      self.inputMarkup.AddFiducial(242,36,0)
      self.inputMarkup.AddFiducial(-26,162,0)
      self.inputMarkup.SetDisplayVisibility(0)
      self.outputVolume = slicer.vtkMRMLScalarVolumeNode()
      slicer.mrmlScene.AddNode(self.outputVolume) 
      self.logic.updateModelFromMarkup(self.inputMarkup,self.clippingModel)
      self.logic.clipVolumeWithModel(self.imageNode, self.clippingModel, True , 255, self.outputVolume)
      self.logic.showInSliceViewers(self.outputVolume, ["Red"])
      self.cropping == 0 
      self.leftMat.SetElement(0,3,-230)
      self.leftMat.SetElement(1,1,-1)
      self.leftMat.SetElement(1,3,520)
      self.leftMat.SetElement(2,2,-1)
      self.leftTransform.PostMultiply()
      self.leftTransform.Identity()  
      self.leftTransform.Concatenate(self.leftMat)  
      self.outputVolume.GetDisplayNode().SetAutoWindowLevel(0)
      self.outputVolume.GetDisplayNode().SetWindowLevelMinMax(25,100)
      self.redWidget.sliceLogic().GetSliceCompositeNode().SetBackgroundVolumeID(self.outputVolume.GetID())
      self.resliceLogic.SetDriverForSlice(self.outputVolume.GetID(), slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed'))
      self.resliceLogic.SetModeForSlice(self.resliceLogic.MODE_TRANSVERSE, slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed'))
      self.clippingModel.SetDisplayVisibility(False)
      slicer.app.layoutManager().sliceWidget('Red').sliceLogic().GetSliceNode().SetSliceVisible(True)
      slicer.app.layoutManager().sliceWidget("Red").sliceController().fitSliceToBackground()
      self.outputVolume.SetAndObserveTransformNodeID(self.InputRegistrationTransformNode.GetID())
      self.InputRegistrationTransformNode.SetMatrixTransformToParent(self.leftTransform.GetMatrix())

  def onImageChanged2(self):
    self.InputRegistrationTransformNodeX = slicer.vtkMRMLLinearTransformNode()
    slicer.mrmlScene.AddNode(self.InputRegistrationTransformNodeX)
    if self.imageNode2 is not None: 
      self.imageNode2.SetAndObserveTransformNodeID(None) 
      self.imageNode2 = None 
      self.imageNode2 = self.imageSelector2.currentNode()
      if self.imageNode2 is None: 
        print('Please select the right volume')
      if self.imageNode2 is not None:
        self.cropping = 1 
        self.imageNode2 = self.imageSelector2.currentNode()
        self.clippingModel2 = slicer.vtkMRMLModelNode()
        self.clippingModel.SetName('Clipping Model 2')
        slicer.mrmlScene.AddNode(self.clippingModel2)
        self.displayNode2 = slicer.vtkMRMLMarkupsDisplayNode()
        slicer.mrmlScene.AddNode(self.displayNode2)
        self.inputMarkup2 = slicer.vtkMRMLMarkupsFiducialNode()
        self.inputMarkup2.SetName('C')
        slicer.mrmlScene.AddNode(self.inputMarkup2)
        self.inputMarkup2.SetAndObserveDisplayNodeID(self.displayNode2.GetID())
        self.inputMarkup2.AddFiducial(234,509,-0.5)
        self.inputMarkup2.AddFiducial(234,509,0.0)
        self.inputMarkup2.AddFiducial(500,130,0)
        self.inputMarkup2.AddFiducial(242,36,0)
        self.inputMarkup2.AddFiducial(-26,162,0)
        self.inputMarkup2.SetDisplayVisibility(0)
        self.outputVolume2 = slicer.vtkMRMLScalarVolumeNode()
        slicer.mrmlScene.AddNode(self.outputVolume2) 
        self.logic.updateModelFromMarkup(self.inputMarkup2,self.clippingModel2)
        self.logic.clipVolumeWithModel(self.imageNode2, self.clippingModel2, True, 255, self.outputVolume2)
        self.logic.showInSliceViewers(self.outputVolume2, ["Yellow"])
        self.cropping == 0       
        self.rightMat.SetElement(0,0,0)
        self.rightMat.SetElement(2,0,-1)
        self.rightMat.SetElement(1,1,-1)
        self.rightMat.SetElement(0,2,-1)
        self.rightMat.SetElement(2,2,0)
        self.rightMat.SetElement(1,3,520)
        self.rightMat.SetElement(2,3,230)
        self.rightTransform.PostMultiply()
        self.rightTransform.Identity()
        self.rightTransform.Concatenate(self.rightMat)
        self.outputVolume2.GetDisplayNode().SetAutoWindowLevel(0)
        self.outputVolume2.GetDisplayNode().SetWindowLevelMinMax(25,100)
        self.yellowWidget.sliceLogic().GetSliceCompositeNode().SetBackgroundVolumeID(self.outputVolume2.GetID())
        self.resliceLogic.SetDriverForSlice(self.outputVolume2.GetID(), slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeYellow'))
        self.resliceLogic.SetModeForSlice(self.resliceLogic.MODE_TRANSVERSE, slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeYellow'))
        self.clippingModel2.SetDisplayVisibility(False)
        slicer.app.layoutManager().sliceWidget('Yellow').sliceLogic().GetSliceNode().SetSliceVisible(True)
        slicer.app.layoutManager().sliceWidget("Yellow").sliceController().fitSliceToBackground()
        self.outputVolume2.SetAndObserveTransformNodeID(self.InputRegistrationTransformNodeX.GetID())
        self.InputRegistrationTransformNodeX.SetMatrixTransformToParent(self.rightTransform.GetMatrix())
    if self.imageNode2 is None:
      self.cropping = 1 
      self.imageNode2 = self.imageSelector2.currentNode()
      self.clippingModel2 = slicer.vtkMRMLModelNode()
      self.clippingModel.SetName('Clipping Model 2')
      slicer.mrmlScene.AddNode(self.clippingModel2)
      self.displayNode2 = slicer.vtkMRMLMarkupsDisplayNode()
      slicer.mrmlScene.AddNode(self.displayNode2)
      self.inputMarkup2 = slicer.vtkMRMLMarkupsFiducialNode()
      self.inputMarkup2.SetName('C')
      slicer.mrmlScene.AddNode(self.inputMarkup2)
      self.inputMarkup2.SetAndObserveDisplayNodeID(self.displayNode2.GetID())
      self.inputMarkup2.AddFiducial(234,509,-0.5)
      self.inputMarkup2.AddFiducial(234,509,0.0)
      self.inputMarkup2.AddFiducial(500,130,0)
      self.inputMarkup2.AddFiducial(242,36,0)
      self.inputMarkup2.AddFiducial(-26,162,0)
      self.inputMarkup2.SetDisplayVisibility(0)
      self.outputVolume2 = slicer.vtkMRMLScalarVolumeNode()
      slicer.mrmlScene.AddNode(self.outputVolume2) 
      self.logic.updateModelFromMarkup(self.inputMarkup2,self.clippingModel2)
      self.logic.clipVolumeWithModel(self.imageNode2, self.clippingModel2, True, 255, self.outputVolume2)
      self.logic.showInSliceViewers(self.outputVolume2, ["Yellow"])
      self.cropping = 0       
      self.rightMat.SetElement(0,0,0)
      self.rightMat.SetElement(2,0,-1)
      self.rightMat.SetElement(1,1,-1)
      self.rightMat.SetElement(0,2,-1)
      self.rightMat.SetElement(2,2,0)
      self.rightMat.SetElement(1,3,520)
      self.rightMat.SetElement(2,3,230)
      self.rightTransform.PostMultiply()
      self.rightTransform.Identity()
      self.rightTransform.Concatenate(self.rightMat)
      self.outputVolume2.GetDisplayNode().SetAutoWindowLevel(0)
      self.outputVolume2.GetDisplayNode().SetWindowLevelMinMax(25,100)
      self.yellowWidget.sliceLogic().GetSliceCompositeNode().SetBackgroundVolumeID(self.outputVolume2.GetID())
      self.resliceLogic.SetDriverForSlice(self.outputVolume2.GetID(), slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeYellow'))
      self.resliceLogic.SetModeForSlice(self.resliceLogic.MODE_TRANSVERSE, slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeYellow'))
      self.clippingModel2.SetDisplayVisibility(False)
      slicer.app.layoutManager().sliceWidget('Yellow').sliceLogic().GetSliceNode().SetSliceVisible(True)
      slicer.app.layoutManager().sliceWidget("Yellow").sliceController().fitSliceToBackground()
      self.outputVolume2.SetAndObserveTransformNodeID(self.InputRegistrationTransformNodeX.GetID())
      self.InputRegistrationTransformNodeX.SetMatrixTransformToParent(self.rightTransform.GetMatrix())

  def onTransformChanged(self):
    if self.transformNode is not None: 
      self.transformNode.SetAndObserveTransformNodeID(None) 
      self.transformNode = None 
    self.transformNode = self.TransformSelector.currentNode() 
    if self.transformNode is None:
      print('Please select a tip to probe transform')
    else:
      self.needleModel.SetAndObserveTransformNodeID(self.TransformSelector.currentNode().GetID()) 

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
          self.sequenceNode3 = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSequenceNode")
          self.sequenceBrowserNode.AddProxyNode(self.transformNode, self.sequenceNode)
          self.sequenceBrowserNode.AddProxyNode(self.imageNode, self.sequenceNode2)
          self.sequenceBrowserNode.AddProxyNode(self.imageNode2,self.sequenceNode3)
          self.sequenceBrowserLogic.AddSynchronizedNode(self.sequenceNode, self.transformNode, self.sequenceBrowserNode)
          self.sequenceBrowserLogic.AddSynchronizedNode(self.sequenceNode2, self.imageNode, self.sequenceBrowserNode)
          self.sequenceBrowserLogic.AddSynchronizedNode(self.sequenceNode3, self.imageNode2, self.sequenceBrowserNode)
          self.sequenceBrowserNode.EndModify(self.modifyFlag)
          self.RecordButton.text = "Recording"
          self.RecordButton.setEnabled(False) 
          self.sequenceBrowserNode.SetRecording(self.sequenceNode, True)
          self.sequenceBrowserNode.SetRecording(self.sequenceNode2, True)
          self.sequenceBrowserNode.SetRecording(self.sequenceNode3, True)
          self.sequenceBrowserNode.SetRecordingActive(True)
      else:
        if self.sequenceBrowserNode.GetRecordingActive() == True:
          self.sequenceBrowserNode.SetRecording(self.sequenceNode, True)
          self.sequenceBrowserNode.SetRecording(self.sequenceNode2, True)
          self.sequenceBrowserNode.SetRecording(self.sequenceNode3, True)
        else: 
          print('The Sequence is currently recording')
          
  def onStopButtonClicked(self): 
    if self.sequenceBrowserNode is not None: 
      if self.sequenceBrowserNode.GetRecordingActive() == True:
        self.RecordButton.text = "Start Recording"
        self.sequenceBrowserNode.SetRecording(self.sequenceNode, False)
        self.sequenceBrowserNode.SetRecording(self.sequenceNode2, False)
        self.sequenceBrowserNode.SetRecording(self.sequenceNode3, False)
        self.sequenceBrowserNode.SetRecordingActive(False)
        self.RecordButton.enabled = True 

  def onSaveButtonClicked(self):
    if self.pathInput.text is None: 
      print('Please enter the file path')
    else:
      print('Files saved')
      self.filePath = str(self.pathInput.text)
      slicer.util.saveScene(self.filePath+'/SlicerSceneUSCalibration.mrml')
      slicer.util.saveNode(self.imageSelector.currentNode(), str(self.pathInput.text)+'/Image_Probe.nrrd')
      slicer.util.saveNode(self.imageSelector2.currentNode(), str(self.pathInput.text)+'/Image_Reference.nrrd')
      slicer.util.saveNode(self.TransformSelector.currentNode(),str(self.pathInput.text)+'/NeedleTipToProbe.h5')
      slicer.util.saveNode(self.sequenceNode, str(self.pathInput.text)+'/Sequence.seq.mha')
      slicer.util.saveNode(self.sequenceNode2, str(self.pathInput.text)+'/Sequence_1.seq.nrrd')
      slicer.util.saveNode(self.sequenceNode3, str(self.pathInput.text)+'/Sequence_2.seq.nrrd')

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
  
  def onVisualizeButtonClicked(self):
    self.clippingModel.SetDisplayVisibility(False)
    if self.imageNode or self.imageNode2 or self.transformNode is None:
      if self.imageNode is None: 
        print('Please select the left image') 
      if self.imageNode2 is None: 
        print('Please select the right image') 
      if self.transformNode is None: 
        print('Please select a tip to probe transform')
    if self.imageNode and self.imageNode2 and self.transformNode is not None:
      self.OutputRegistrationTransformNode = slicer.vtkMRMLLinearTransformNode() 
      self.OutputRegistrationTransformNodeX = slicer.vtkMRMLLinearTransformNode()
      slicer.mrmlScene.AddNode(self.OutputRegistrationTransformNode)
      slicer.mrmlScene.AddNode(self.OutputRegistrationTransformNodeX)
      self.OutputRegistrationTransformNode.SetName('ImageToProbe')
      self.OutputRegistrationTransformNodeX.SetName('ImageToProbeX')
      if self.fiducialNode is not None:
        self.fiducialNode.RemoveAllMarkups()
      if self.isVisualizing:
        slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutSideBySideView)    
        self.isVisualizing = False
        self.visualizeButton.text = 'Show 3D Scene'
        self.OutputRegistrationTransformNode.SetMatrixTransformToParent(None)
        self.OutputRegistrationTransformNodeX.SetMatrixTransformToParent(None)
      else:
        self.isVisualizing = True
        slicer.app.layoutManager().sliceWidget('Red').sliceLogic().GetSliceNode().SetSliceVisible(True)
        slicer.app.layoutManager().sliceWidget('Yellow').sliceLogic().GetSliceNode().SetSliceVisible(True)     
        slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUp3DView)
        self.visualizeButton.text = 'Show ultrasound stream'
        if self.imageSelector.currentNode is None: 
          print('Please select an US volume')
        else:
          self.leftTransform.Concatenate(self.ImageToProbe)
          self.rightTransform.Concatenate(self.ImageToProbe)
          self.imageSelector.currentNode().SetAndObserveTransformNodeID(self.OutputRegistrationTransformNode.GetID())
          self.imageSelector2.currentNode().SetAndObserveTransformNodeID(self.OutputRegistrationTransformNodeX.GetID())
          self.OutputRegistrationTransformNode.SetMatrixTransformToParent(self.leftTransform.GetMatrix())
          self.OutputRegistrationTransformNodeX.SetMatrixTransformToParent(self.rightTransform.GetMatrix())

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

  def onFiducialClicked(self):
    if self.imageNode or self.imageNode2 or self.transformNode is None: 
      if self.imageNode is None: 
        print('Please select an US volume')
      if self.transformNode is None:
        print('Please select the tip to probe transform')
      if self.imageNode2 is None: 
        print('Please select the right volume')
    if self.imageNode and self.imageNode2 and self.transformNode is not None:
      if self.fiducialNode is not None: 
          self.fiducialNode.RemoveAllMarkups()
      self.numFid = self.numFid +1
      self.numFidLabel.setText(str(self.numFid))
      slicer.modules.markups.logic().StartPlaceMode(0)
      self.redWidget.setCursor(qt.QCursor(2))
      self.yellowWidget.setCursor(qt.QCursor(2))
      if self.fidCount == 0: 
        slicer.modules.markups.logic().StartPlaceMode(0)
        self.redWidget.setCursor(qt.QCursor(2))
        self.yellowWidget.setCursor(qt.QCursor(2))
    
class XPlaneCalibrationLogic(ScriptedLoadableModuleLogic):
  def __init__(self):
    self.manualRegLogic = slicer.vtkSlicerPointToLineRegistrationLogic()
    self.autoRegLogic = slicer.vtkSlicerPointToLineRegistrationLogic()
    self.manualRegLogic.SetLandmarkRegistrationModeToSimilarity()
    self.autoRegLogic.SetLandmarkRegistrationModeToSimilarity()

  def AddPointAndLineMan(self, point, lineOrigin, lineDirection):
    self.manualRegLogic.AddPointAndLine(point, lineOrigin, lineDirection)
  
  def AddPointAndLineAuto(self, point, lineOrigin, lineDirection):
    self.autoRegLogic.AddPointAndLine(point, lineOrigin, lineDirection)
    
  def clipVolumeWithModel(self, inputVolume, clippingModel, clipOutsideSurface, fillValue, outputVolume):
    """
    Fill voxels of the input volume inside/outside the clipping model with the provided fill value
    """
    
    # Determine the transform between the box and the image IJK coordinate systems
    
    rasToModel = vtk.vtkMatrix4x4()    
    if clippingModel.GetTransformNodeID() != None:
      modelTransformNode = slicer.mrmlScene.GetNodeByID(clippingModel.GetTransformNodeID())
      boxToRas = vtk.vtkMatrix4x4()
      modelTransformNode.GetMatrixTransformToWorld(boxToRas)
      rasToModel.DeepCopy(boxToRas)
      rasToModel.Invert()
      
    ijkToRas = vtk.vtkMatrix4x4()
    inputVolume.GetIJKToRASMatrix( ijkToRas )

    ijkToModel = vtk.vtkMatrix4x4()
    vtk.vtkMatrix4x4.Multiply4x4(rasToModel,ijkToRas,ijkToModel)
    modelToIjkTransform = vtk.vtkTransform()
    modelToIjkTransform.SetMatrix(ijkToModel)
    modelToIjkTransform.Inverse()
    
    transformModelToIjk=vtk.vtkTransformPolyDataFilter()
    transformModelToIjk.SetTransform(modelToIjkTransform)
    transformModelToIjk.SetInputConnection(clippingModel.GetPolyDataConnection())

    # Use the stencil to fill the volume
    
    # Convert model to stencil
    polyToStencil = vtk.vtkPolyDataToImageStencil()
    polyToStencil.SetInputConnection(transformModelToIjk.GetOutputPort())
    polyToStencil.SetOutputSpacing(inputVolume.GetImageData().GetSpacing())
    polyToStencil.SetOutputOrigin(inputVolume.GetImageData().GetOrigin())
    polyToStencil.SetOutputWholeExtent(inputVolume.GetImageData().GetExtent())
    
    # Apply the stencil to the volume
    stencilToImage=vtk.vtkImageStencil()
    stencilToImage.SetInputConnection(inputVolume.GetImageDataConnection())
    stencilToImage.SetStencilConnection(polyToStencil.GetOutputPort())
    if clipOutsideSurface:
      stencilToImage.ReverseStencilOff()
    else:
      stencilToImage.ReverseStencilOn()
    stencilToImage.SetBackgroundValue(fillValue)
    stencilToImage.Update()

    # Update the volume with the stencil operation result
    outputImageData = vtk.vtkImageData()
    outputImageData.DeepCopy(stencilToImage.GetOutput())
    
    outputVolume.SetAndObserveImageData(outputImageData);
    outputVolume.SetIJKToRASMatrix(ijkToRas)

    # Add a default display node to output volume node if it does not exist yet
    if not outputVolume.GetDisplayNode:
      displayNode=slicer.vtkMRMLScalarVolumeDisplayNode()
      displayNode.SetAndObserveColorNodeID("vtkMRMLColorTableNodeGrey")
      slicer.mrmlScene.AddNode(displayNode)
      outputVolume.SetAndObserveDisplayNodeID(displayNode.GetID())

    return True
    
  def updateModelFromMarkup(self, inputMarkup, outputModel):
    """
    Update model to enclose all points in the input markup list
    """
    
    # Delaunay triangulation is robust and creates nice smooth surfaces from a small number of points,
    # however it can only generate convex surfaces robustly.
    useDelaunay = True
    
    # Create polydata point set from markup points
    
    points = vtk.vtkPoints()
    cellArray = vtk.vtkCellArray()
    
    numberOfPoints = inputMarkup.GetNumberOfFiducials()
    
    # Surface generation algorithms behave unpredictably when there are not enough points
    # return if there are very few points
    if useDelaunay:
      if numberOfPoints<3:
        return
    else:
      if numberOfPoints<10:
        return

    points.SetNumberOfPoints(numberOfPoints)
    new_coord = [0.0, 0.0, 0.0]

    for i in range(numberOfPoints):
      inputMarkup.GetNthFiducialPosition(i,new_coord)
      points.SetPoint(i, new_coord)

    cellArray.InsertNextCell(numberOfPoints)
    for i in range(numberOfPoints):
      cellArray.InsertCellPoint(i)

    pointPolyData = vtk.vtkPolyData()
    pointPolyData.SetLines(cellArray)
    pointPolyData.SetPoints(points)

    
    # Create surface from point set

    if useDelaunay:
          
      delaunay = vtk.vtkDelaunay3D()
      delaunay.SetInputData(pointPolyData)

      surfaceFilter = vtk.vtkDataSetSurfaceFilter()
      surfaceFilter.SetInputConnection(delaunay.GetOutputPort())

      smoother = vtk.vtkButterflySubdivisionFilter()
      smoother.SetInputConnection(surfaceFilter.GetOutputPort())
      smoother.SetNumberOfSubdivisions(3)
      smoother.Update()

      outputModel.SetPolyDataConnection(smoother.GetOutputPort())
      
    else:
      
      surf = vtk.vtkSurfaceReconstructionFilter()
      surf.SetInputData(pointPolyData)
      surf.SetNeighborhoodSize(20)
      surf.SetSampleSpacing(80) # lower value follows the small details more closely but more dense pointset is needed as input

      cf = vtk.vtkContourFilter()
      cf.SetInputConnection(surf.GetOutputPort())
      cf.SetValue(0, 0.0)

      # Sometimes the contouring algorithm can create a volume whose gradient
      # vector and ordering of polygon (using the right hand rule) are
      # inconsistent. vtkReverseSense cures this problem.
      reverse = vtk.vtkReverseSense()
      reverse.SetInputConnection(cf.GetOutputPort())
      reverse.ReverseCellsOff()
      reverse.ReverseNormalsOff()

      outputModel.SetPolyDataConnection(reverse.GetOutputPort())

    # Create default model display node if does not exist yet
    if not outputModel.GetDisplayNode():
      modelDisplayNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLModelDisplayNode")
      modelDisplayNode.SetColor(0,0,0) # Blue
      modelDisplayNode.BackfaceCullingOff()
      modelDisplayNode.SliceIntersectionVisibilityOn()
      modelDisplayNode.SetOpacity(1) # Between 0-1, 1 being opaque
      slicer.mrmlScene.AddNode(modelDisplayNode)
      outputModel.SetAndObserveDisplayNodeID(modelDisplayNode.GetID())
  
    outputModel.GetDisplayNode().SliceIntersectionVisibilityOn()
      
    outputModel.Modified()

  def showInSliceViewers(self, volumeNode, sliceWidgetNames):
    # Displays volumeNode in the selected slice viewers as background volume
    # Existing background volume is pushed to foreground, existing foreground volume will not be shown anymore
    # sliceWidgetNames is a list of slice view names, such as ["Yellow", "Green"]
    if not volumeNode:
      return
    newVolumeNodeID = volumeNode.GetID()
    for sliceWidgetName in sliceWidgetNames:
      sliceLogic = slicer.app.layoutManager().sliceWidget(sliceWidgetName).sliceLogic()
      foregroundVolumeNodeID = sliceLogic.GetSliceCompositeNode().GetForegroundVolumeID()
      backgroundVolumeNodeID = sliceLogic.GetSliceCompositeNode().GetBackgroundVolumeID()
      if foregroundVolumeNodeID == newVolumeNodeID or backgroundVolumeNodeID == newVolumeNodeID:
        # new volume is already shown as foreground or background
        continue
      if backgroundVolumeNodeID:
        # there is a background volume, push it to the foreground because we will replace the background volume
        sliceLogic.GetSliceCompositeNode().SetForegroundVolumeID(backgroundVolumeNodeID)
      # show the new volume as background
      sliceLogic.GetSliceCompositeNode().SetBackgroundVolumeID(newVolumeNodeID)