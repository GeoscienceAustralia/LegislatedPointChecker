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

        # parameters[0] == in_layer
        in_layer = arcpy.Parameter(
            displayName="Input Layer",
            name="in_layer",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        in_layer.filter.list = ["Point"]
        params.append(in_layer)

        # parameters[1] == compare_geom_dms
        compare_geom_dms = arcpy.Parameter(
            displayName="Compare DMS to geometry?",
            name="compare_geom_dms",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        compare_geom_dms.value = True
        params.append(compare_geom_dms)

        # parameters[2] == lat_dms_field
        lat_dms_field = arcpy.Parameter(
            displayName="Field with latitude in DMS format",
            name="lat_dms_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        lat_dms_field.parameterDependencies = [in_layer.name]
        params.append(lat_dms_field)

        # parameters[3] == lon_dms_field
        lon_dms_field = arcpy.Parameter(
            displayName="Field with longitude in DMS format",
            name="lon_dms_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        lon_dms_field.parameterDependencies = [in_layer.name]
        params.append(lon_dms_field)

        # parameters[4] == compare_geom_dd
        compare_geom_dd = arcpy.Parameter(
            displayName="Compare DD to geometry?",
            name="compare_geom_dd",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        compare_geom_dd.value = True
        params.append(compare_geom_dd)

        # parameters[5] == lat_dd_field
        lat_dd_field = arcpy.Parameter(
            displayName="Field with latitude in DD format",
            name="lat_dd_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        lat_dd_field.parameterDependencies = [in_layer.name]
        params.append(lat_dd_field)

        # parameters[6] == lon_dd_field
        lon_dd_field = arcpy.Parameter(
            displayName="Field with longitude in DD format",
            name="lon_dd_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        lon_dd_field.parameterDependencies = [in_layer.name]
        params.append(lon_dd_field)

        # parameters[7] == compare_dms_dd
        compare_dms_dd = arcpy.Parameter(
            displayName="Compare DMS to DD?",
            name="compare_dms_dd",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        compare_dms_dd.value = True
        params.append(compare_dms_dd)
        
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
                parameters[2].value = 'SRLTDMS'
            if 'SRLNDMS' in param0_fieldnames:
                parameters[3].value = 'SRLNDMS'
            if 'COORLT' in param0_fieldnames:
                parameters[5].value = 'COORLT'
            if 'COORLN' in param0_fieldnames:
                parameters[6].value = 'COORLN'
            if 'COORLO' in param0_fieldnames:  # sometimes this field name is used
                parameters[6].value = 'COORLO'
        
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcpy.AddMessage("checking " + parameters[0].valueAsText)
        
        import math

        def dd_to_dms(dd):
            """ Converts floating point decimal degree to "ddd mm ss.ssss" string

            :param dd: float representing decimal degrees
            :type dd: float
            :return: The string containing "ddd mm ss.ssss"
            :rtype: string

            """

            # calculate the d, m, s values
            is_positive = dd >= 0
            dd = abs(dd)
            m, s = divmod(dd * 3600, 60)
            d, m = divmod(m, 60)
            d = d if is_positive else -d
            s = round(s, 4)
            dms = " ".join((str(int(d)), str(int(m)).zfill(2), str(s)))
            return dms
        
        def dms_to_dd(dms):
            """ Converts "ddd mm ss.ssss" string to floating point decimal degree
            
            :param dms: The string containing "ddd mm ss.ssss"
            :type dms: String
            :return: The string converted into signed floating point representation
            :rtype: Float

            """

            # check if the separator for the dms string is ' ' or '-'
            separator = None
            try:
                if dms.count('-') >= 2:
                    separator = '-'
                elif dms.count(' ') >= 2:
                    separator = ' '
            except ValueError:
                print("Error: dms separator isn't ' ' or '-'")

            # if '-' is the separator then drop the first part
            if separator == '-':
                if len(dms.split(sep=separator)) == 4:
                    _, d, m, s = dms.split(sep=separator)
                else:
                    d, m, s = dms.split(sep=separator)
            else:
                d, m, s = dms.split(sep=separator)

            # calculate the dd value
            dd = abs(float(d)) + float(m)/60 + float(s)/(60*60)

            # make float dd negative if degree is negative or if dms starts with '-'
            if float(d) < 1 or dms[0] == '-':
                dd *= -1

            return dd
        
        # define the fields that are being compared
        oid_fieldname = arcpy.Describe(parameters[0].valueAsText).OIDFieldName
        field_list = [oid_fieldname,              # row[0] OID
                      parameters[2].valueAsText,  # row[1] lat_dms_field
                      parameters[3].valueAsText,  # row[2] lon_dms_field
                      parameters[5].valueAsText,  # row[3] lat_dd_field
                      parameters[6].valueAsText,  # row[4] lon_dd_field
                      "SHAPE@"]                   # row[5] geometry
                      
        # make the cursor
        with arcpy.da.SearchCursor(parameters[0].valueAsText, field_list) as cursor:
            # loop through features
            for row in cursor:
            
                # if no lat DMS defined
                if row[1] is None:  # lat_dms_field
                    print("no latitude DMS value")
                    dms_lat_isclose = True
                else:
                    # check dms lat isclose to geom lat
                    dms_lat_isclose = math.isclose(dms_to_dd(row[1]), row[5][0].Y, abs_tol=1e-8)

                # if no lon DMS defined
                if row[2] is None:  # lon_dms_field
                    print("no longitude DMS value")
                    dms_lon_isclose = True
                else:
                    # check dms long isclose to geom long
                    dms_lon_isclose = math.isclose(dms_to_dd(row[2]), row[5][0].X, abs_tol=1e-8)

                # check dd lat isclose to geom lat
                dd_lat_isclose = math.isclose(float(row[3]), row[5][0].Y, abs_tol=1e-8)

                # check dd long isclose to geom long
                dd_lon_isclose = math.isclose(float(row[4]), row[5][0].X, abs_tol=1e-8)
                        
                # check if dms isclose to dd lat
                dms_dd_lat_isclose = math.isclose(dms_to_dd(row[1]), float(row[3]), abs_tol=1e-8)

                # check if dms isclose to dd long
                dms_dd_long_isclose = math.isclose(dms_to_dd(row[2]), float(row[4]), abs_tol=1e-8)

                # send results to user

                # report geom vs DMS
                if parameters[1].value:
                    # if lat isn't close: error
                    if not dms_lat_isclose:
                        arcpy.AddError("feature: " + str(row[0]) +
                                       " Lat DMS:" + str(row[1]) +
                                       " Lat geometry:" + str(dd_to_dms(row[5][0].Y)))
                    # if lon isn't close: error
                    if not dms_lon_isclose:
                        arcpy.AddError("feature: " + str(row[0]) +
                                       " Long DMS:" + str(row[2]) +
                                       " Long geometry:" + str(dd_to_dms(row[5][0].X)))

                # report geom vs DD
                if parameters[4].value:
                    if not dd_lat_isclose:
                        arcpy.AddError("feature: " + str(row[0]) +
                                       " Lat DD:" + str(row[3]) +
                                       " Lat geometry:" + str(row[5][0].Y))
                    if not dd_lon_isclose:
                        arcpy.AddError("feature: " + str(row[0]) +
                                       " Long DD: " + str(row[4]) +
                                       " Long geometry:" + str(row[5][0].Y))

                # report DMS vs DD
                if parameters[7].value:
                    if not dms_dd_lat_isclose:
                        arcpy.AddError("feature: " + str(row[0]) +
                                       " Lat DMS:" + str(row[1]) +
                                       " Lat DD:" + str(dd_to_dms(row[3])))
                    if not dms_dd_long_isclose:
                        arcpy.AddError("feature: " + str(row[0]) +
                                       " Long DMS:" + str(row[2]) +
                                       " Long DD: " + str(dd_to_dms(row[4])))
