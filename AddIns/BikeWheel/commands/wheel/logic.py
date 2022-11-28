from enum import Enum
from math import pi
  
from ..spoke import logic as Spoke
from ..rim import logic as Rim
from ..hub import logic as Hub

import adsk.core as core
import adsk.fusion as fusion

app = core.Application.get()
if app:
    ui = app.userInterface
    createPoint = core.Point3D.create
    alert = ui.messageBox
design = fusion.Design.cast(app.activeProduct)
if not design:
    alert('You must be in the design workspace to use this command')
skipValidate = False

class SpokeType(Enum):
    BUTTEDSTRAIGHT = 1
    BUTTEDJ = 2
    BLADEDSTRAIGHT = 3
    BLADEDJ = 4

class WheelLogic():
    def __init__(self) -> None:
        self.hub = ""
        self.spokeQuantity = 32
        self.spokeType = SpokeType.BUTTEDJ
        self.rim = ""
        self.rimSize = "700c"
    
    def CreateCommandInputs(self, inputs: core.CommandInputs):
        global skipValidate
        skipValidate = True

        self.hubInput: core.DropDownCommandInput = inputs.addDropDownCommandInput(
            "hub", "Hub", core.DropDownStyles.TextListDropDownStyle
        )
        for hub in Hub.hubData:
            self.hubInput.listItems.add(hub, False)

        self.rimInput: core.DropDownCommandInput = inputs.addDropDownCommandInput('rim', 'Rim', core.DropDownStyles.TextListDropDownStyle)
        for rim in Rim.rimProfiles:
            self.rimInput.listItems.add(rim, False)

        self.sizeInput: core.DropDownCommandInput = inputs.addDropDownCommandInput('size', 'Size', core.DropDownStyles.TextListDropDownStyle)
        # rimSizes = Rim.rimProfiles[self.rimInput.selectedItem.name]['sizes'].keys()
        # for size in rimSizes:
            # self.sizeInput.listItems.add(size, False)

        self.spokesInput: core.DropDownCommandInput = inputs.addDropDownCommandInput('spokes', 'Spokes', core.DropDownStyles.TextListDropDownStyle)
        # spokeCounts = Rim.rimProfiles[self.rimInput.selectedItem.name]['spokes']
        # for count in spokeCounts:
            # self.spokesInput.listItems.add(str(count), False)

        self.buttedInput: core.BoolValueCommandInput = inputs.addBoolValueInput('butted', 'Butted', True, '', False)
        # self.straightPullInput: core.BoolValueCommandInput = inputs.addBoolValueInput('straightPull', 'Straight Pull', True, '', False)
        # self.bladedInput: core.BoolValueCommandInput = inputs.addBoolValueInput('bladed', 'Bladed', True, '', False)
        self.diameterInput: core.DropDownCommandInput = inputs.addDropDownCommandInput('diameter', 'Diameter', core.DropDownStyles.TextListDropDownStyle)
        self.diameterInput.listItems.add('1.8 mm', False)
        self.diameterInput.listItems.add('2.0 mm', True)
        self.diameterInput.listItems.add('2.3 mm', False)
        self.diameterInput.listItems.add('2.6 mm', False)

        self.errorMessageTextInput = inputs.addTextBoxCommandInput('errMessage', '', '', 2, True)
        self.errorMessageTextInput.isFullWidth = True

        skipValidate = False

    def HandleInputsChanged(self, args: core.InputChangedEventArgs):
        changedInput = args.input
        
        if not skipValidate:
            if changedInput.id == 'rim':
                self.sizeInput.listItems.clear()
                self.spokesInput.listItems.clear()
                rimSizes = Rim.rimProfiles[self.rimInput.selectedItem.name]['sizes'].keys()
                for size in rimSizes:
                    self.sizeInput.listItems.add(size, False)
                spokeCounts = Rim.rimProfiles[self.rimInput.selectedItem.name]['spokes']
                for count in spokeCounts:
                    self.spokesInput.listItems.add(str(count), False)

    def HandleValidateInputs(self, args: core.ValidateInputsEventArgs):
        unitsMgr = design.unitsManager
        if not skipValidate:
            self.errorMessageTextInput.text = ''
            self.hub = self.hubInput.selectedItem.name
            self.rim = self.rimInput.selectedItem.name
            self.size = self.sizeInput.selectedItem.name
            self.spokes = int(self.spokesInput.selectedItem.name)
            # if not self.lengthInput.isValidExpression:
            #     self.errorMessageTextInput.text = 'The spoke length is invalid'
            #     args.areInputsValid = False
            #     return
                     
            # if self.lengthInput.value < 10 or self.lengthInput.value > 50:
            #     self.errorMessageTextInput.text = 'The spoke length should be between 100 and 500 mm'
            #     args.areInputsValid = False
            #     return
            # if self.bladedInput.value == True and self.buttedInput.value == True:
            #     self.errorMessageTextInput.text = 'Bladed and Butted cannot both be checked'
            #     args.areInputsValid = False
            #     return
            # args.areInputsValid = True
            # self.bladed = self.bladedInput.value
            # self.butted = self.buttedInput.value
            # self.length = unitsMgr.evaluateExpression(self.lengthInput.expression)
            # self.diameter = unitsMgr.evaluateExpression(self.diameterInput.selectedItem.name)
            # self.straightPull = self.straightPullInput.value

    def HandleExecute(self, args: core.CommandEventArgs):
        unitsMgr = design.unitsManager

        self.hub_logic = Hub.HubLogic()
        self.hub_logic.hubType = Hub.hubData[self.hub]["type"]
        self.hub_logic.brakeType = Hub.hubData[self.hub]["brake"]
        self.hub_logic.axleType = Hub.hubData[self.hub]["axle"]
        self.hub_logic.axleDia = Hub.axleDiameters[self.hub_logic.hubType][self.hub_logic.axleType]
        self.hub_logic.old = Hub.hubData[self.hub]["old"]
        self.hub_logic.leftFlangeDia = Hub.hubData[self.hub]["leftFlangeDia"]
        self.hub_logic.rightFlangeDia = Hub.hubData[self.hub]["rightFlangeDia"]
        self.hub_logic.centerToLeftFlange = Hub.hubData[self.hub]["centerToLeftFlange"]
        self.hub_logic.centerToRightFlange = Hub.hubData[self.hub]["centerToRightFlange"]
        self.hub_logic.spokes = self.spokes

        self.spoke_logic = Spoke.SpokeLogic()
        # self.bladed = self.bladedInput.value
        self.spoke_logic.butted = self.buttedInput.value
        self.length = {} # TODO calculate this length
        self.diameter = unitsMgr.evaluateExpression(self.diameterInput.selectedItem.name)
        # self.straightPull = self.straightPullInput.value

        self.rim_logic = Rim.RimLogic()
        self.rim_logic.rimProfilePath = f'{self.resource_dir}{Rim.rimProfiles[self.rim]["profile"]}'
        self.rim_logic.rim = self.rim
        self.rim_logic.size = self.size
        self.rim_logic.spokeCount = self.spokes

        createWheel(self)

def createWheel(self: WheelLogic):
    Hub.createHub(self.hub_logic)
    Rim.createRim(self.rim_logic)
    Spoke.createSpoke(self.spoke_logic)
