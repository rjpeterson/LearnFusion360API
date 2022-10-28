#Author-
#Description-

import csv
import adsk.core as core, adsk.fusion as fusion, adsk.cam, traceback

def run(context):
    ui = None
    try:
        app = core.Application.get()
        ui  = app.userInterface
        # ui.messageBox('Hello script')
        design: fusion.Design = app.activeProduct
        document: core.Document = app.activeDocument
        alert = ui.messageBox

        # Get project folder
        path = design.parentDocument.dataFile.parentFolder
        baseName = document.dataFile.name

        data = app.data
        activeHub = data.activeHub

        # The long way round
        # projFilesProject: core.DataProject = None
        # for proj in activeHub.dataProjects:
        #     if proj.name == 'Tutorials':
        #         projFilesProject = proj
        #         break
        # projFolder = projFilesProject.rootFolder.dataFolders.itemByName("API")
        # cabinetFile = projFilesProject.rootFolder.dataFiles.item(0)

        # The short way
        cabinetFile = path.dataFiles.item(0)

        # ui.messageBox(f'{cabinetFile.name} {cabinetFile.id}')
        # ui.messageBox(f'{path.name} {path.id}')

        file = open('D:\Documents\Code\Python\Fusion360\Scripts\APICabinetDoorConfig\cabinet.csv')
        # for line in file:
        #     vals = line.split(',')
        #     length = vals[0]
        #     width = vals[1]
        #     alert(f'length: {length} width: {width}')
        with file:
            reader = list(csv.reader(file))

        for csvData in reader:
            length = csvData[0]
            width = csvData[1]

            # Set user params from csv file
            csvParams = design.userParameters
            csvParams.itemByName('length').expression = length
            csvParams.itemByName('width').expression = width
            
            newFileName = f'{baseName} - {length} x {width}'
            document.saveAs(newFileName, path, 'Description', 'Tag')
            # alert("...")

        # Set a new file name


    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
