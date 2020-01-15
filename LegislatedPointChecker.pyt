import arcpy


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = "Legislated Point Checker"

        # List of tool classes associated with this toolbox
        self.tools = [CompareFields]


class CompareFields(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Legislated Point Checker"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        params = []
        
        in_layer = arcpy.Parameter(
            displayName="Input Layer",
            name="in_layer",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        in_layer.filter.list = ["Point"]
        params.append(in_layer)
        
        lat_dms_field = arcpy.Parameter(
            displayName="Field with latitude in dms format",
            name="lat_dms_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        lat_dms_field.parameterDependencies = [in_layer.name]
        params.append(lat_dms_field)
        
        lat_dd_field = arcpy.Parameter(
            displayName="Field with latitude in DD format",
            name="lat_dd_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        lat_dd_field.parameterDependencies = [in_layer.name]
        params.append(lat_dd_field)
        
        lon_dms_field = arcpy.Parameter(
            displayName="Field with longitude in dms format",
            name="lon_dms_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        lon_dms_field.parameterDependencies = [in_layer.name]
        params.append(lon_dms_field)
        
        lon_dd_field = arcpy.Parameter(
            displayName="Field with longitude in DD format",
            name="lon_dd_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        lon_dd_field.parameterDependencies = [in_layer.name]
        params.append(lon_dd_field)
        
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        
        # when the input layer is set, the default field names are populated
        # the field names can be changed by the user, but the default should be correct
        if parameters[0].altered:
            param0_fieldnames = [field.name for field in arcpy.ListFields(parameters[0].valueAsText)]
            if 'SRLTDMS' in param0_fieldnames:
                parameters[1].value = 'SRLTDMS'
            if 'COORLT' in param0_fieldnames:
                parameters[2].value = 'COORLT'
            if 'SRLNDMS' in param0_fieldnames:
                parameters[3].value = 'SRLNDMS'
            if 'COORLN' in param0_fieldnames:
                parameters[4].value = 'COORLN'
        
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcpy.AddMessage("checking " + parameters[0].valueAsText)
        
        import math
        
        def dms_to_dd(dms):
            """ Converts "ddd mm ss.ssss" string to floating point decimal degree
            
            :param dms: The string containing "ddd mm ss.ssss"
            :type dms: String
            :return: The string converted into signed floating point representation
            :rtype: Float

            """
            
            d, m, s = dms.split()
            dd = abs(float(d)) + float(m)/60 + float(s)/(60*60)
            if float(d) < 1:
                dd *= -1
            return dd
        
        # define the fields that are being compared
        field_list = [parameters[1].valueAsText,  # row[0] lat_dms_field
                      parameters[2].valueAsText,  # row[1] lat_dd_field
                      parameters[3].valueAsText,  # row[2] lon_dms_field
                      parameters[4].valueAsText,  # row[3] lon_dd_field
                      "SHAPE@"]                  # row[4] geometry
                      
        # make the cursor
        with arcpy.da.SearchCursor(parameters[0].valueAsText, field_list) as cursor:
            # loop through features
            for row in cursor:
            
                # if no lat defined: pass
                if row[0] is None:
                    lat_isclose = True
                # if lat defined: check dms isclose to DD
                else:
                    lat_isclose = math.isclose(dms_to_dd(row[0]), row[1], abs_tol=1e-8)
                    # if dms isclose to DD check if shape geometry isclose to dms
                    if lat_isclose:
                        lat_isclose = math.isclose(dms_to_dd(row[0]), row[4][0].Y, abs_tol=1e-8)
                    
                # if no lon defined: pass
                if row[2] is None:
                    lon_isclose = True
                # if lat defined: check dms isclose to DD
                else:
                    lon_isclose = math.isclose(dms_to_dd(row[2]), row[3], abs_tol=1e-8)
                    # if dms isclose to DD check if shape geometry isclose to dms
                    if lon_isclose:
                        lon_isclose = math.isclose(dms_to_dd(row[2]), row[4][0].X, abs_tol=1e-8)
                        
                # send results to user
                # if lat isn't close: error
                if not lat_isclose:
                    arcpy.AddError("Latitude dms: " + str(row[0]) +
                                   " DD: " + str(row[1]) +
                                   " geometry: " + str(row[4][0].Y))
                # if lon isn't close: error
                elif not lon_isclose:
                    arcpy.AddError("Longitude dms: " + str(row[2]) +
                                   " DD: " + str(row[3]) +
                                   " geometry: " + str(row[4][0].X))
                # if lat and lon are close: message
                else:
                    arcpy.AddMessage("point passed")
