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

        # parameters[8] == create_xls
        create_xls = arcpy.Parameter(
            displayName="Create Excel Report?",
            name="create_xls",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        create_xls.value = True
        params.append(create_xls)
        
        return params

        # parameters[0] == in_layer
        # parameters[1] == compare_geom_dms
        # parameters[2] == lat_dms_field
        # parameters[3] == lon_dms_field
        # parameters[4] == compare_geom_dd
        # parameters[5] == lat_dd_field
        # parameters[6] == lon_dd_field
        # parameters[7] == compare_dms_dd
        # parameters[8] == create_xls

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
                arcpy.AddError("Error: dms separator isn't ' ' or '-'")

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
        field_list = ["OID@",                     # row[0] oid
                      parameters[2].valueAsText,  # row[1] lat_dms_field
                      parameters[3].valueAsText,  # row[2] lon_dms_field
                      parameters[5].valueAsText,  # row[3] lat_dd_field
                      parameters[6].valueAsText,  # row[4] lon_dd_field
                      "SHAPE@"]                   # row[5] geometry
                      
        # make the cursor
        row_counter = 0
        with arcpy.da.SearchCursor(parameters[0].valueAsText, field_list) as cursor:

            # prepare the excel workbook for output
            if parameters[8].value:
                import xlwt
                # make a workbook object
                wb = xlwt.Workbook()
                # make a worksheet in the workbook
                ws = wb.add_sheet("LegislatedPointChecker")  # len(name) <= 31
                # write the header with the fields assigned by the input parameters
                for i in range(len(field_list)):
                    ws.write(row_counter, i, field_list[i])
                # add extra fields for the tests
                # TODO: only write the fields that are tested
                extra_fields = ["DMS vs Geom",
                                "DD vs Geom",
                                "DMS vs DD"]
                for i in range(len(extra_fields)):
                    ws.write(row_counter, i + len(field_list), extra_fields[i])

                # define green and red styles
                green_style = xlwt.easyxf('pattern: pattern solid, pattern_fore_colour lime, pattern_back_colour lime')
                red_style = xlwt.easyxf('pattern: pattern solid, pattern_fore_colour rose, pattern_back_colour rose')

                # full field list in excel spreadsheet:
                # 0  oid
                # 1  lat_dms_field
                # 2  lon_dms_field
                # 3  lat_dd_field
                # 4  lon_dd_field
                # 5  geometry
                # 6  DMS vs Geom
                # 7  DD vs Geom
                # 8  DMS vs DD

            # parameters[0] == in_layer
            # parameters[1] == compare_geom_dms
            # parameters[2] == lat_dms_field
            # parameters[3] == lon_dms_field
            # parameters[4] == compare_geom_dd
            # parameters[5] == lat_dd_field
            # parameters[6] == lon_dd_field
            # parameters[7] == compare_dms_dd
            # parameters[8] == create_xls

            # loop through features
            for row in cursor:
                row_counter += 1

                # compare DMS to Geometry
                if parameters[1].value or parameters[7].value:

                    # if no lat DMS defined
                    if row[1] is None or row[1] == " ":  # lat_dms_field
                        arcpy.AddError("no latitude DMS value")
                        dms_geom_lat_isclose = False
                    else:
                        # check dms lat isclose to geom lat
                        dms_geom_lat_isclose = math.isclose(dms_to_dd(row[1]), row[5][0].Y, abs_tol=1e-8)

                    # if no lon DMS defined
                    if row[2] is None or row[2] == " ":  # lon_dms_field
                        arcpy.AddError("no longitude DMS value")
                        dms_geom_lon_isclose = False
                    else:
                        # check dms long isclose to geom long
                        dms_geom_lon_isclose = math.isclose(dms_to_dd(row[2]), row[5][0].X, abs_tol=1e-8)

                # compare DD to Geometry
                if parameters[4].value or parameters[7].value:

                    # check dd lat isclose to geom lat
                    try:
                        dd_geom_lat_isclose = math.isclose(float(row[3]), row[5][0].Y, abs_tol=1e-8)
                    except (ValueError, TypeError):
                        dd_geom_lat_isclose = False
                        arcpy.AddError("no latitude DD value")

                    # check dd long isclose to geom long
                    try:
                        dd_geom_lon_isclose = math.isclose(float(row[4]), row[5][0].X, abs_tol=1e-8)
                    except (ValueError, TypeError):
                        dd_geom_lat_isclose = False
                        arcpy.AddError("no longitude DD value")
                        
                # compare DD to DMS
                if parameters[7].value:

                    # check if dms isclose to dd lat
                    try:
                        dms_dd_lat_isclose = math.isclose(dms_to_dd(row[1]), float(row[3]), abs_tol=1e-8)
                    except (ValueError, TypeError):
                        dms_dd_lat_isclose = False

                    # check if dms isclose to dd long
                    try:
                        dms_dd_long_isclose = math.isclose(dms_to_dd(row[2]), float(row[4]), abs_tol=1e-8)
                    except (ValueError, TypeError):
                        dms_dd_long_isclose = False

                # send results to user

                # print geom vs DMS
                if parameters[1].value:
                    # if lat isn't close: error
                    if not dms_geom_lat_isclose:
                        arcpy.AddError("feature: " + str(row[0]) +
                                       " Lat DMS:" + str(row[1]) +
                                       " Lat geometry:" + str(dd_to_dms(row[5][0].Y)))
                    # if lon isn't close: error
                    if not dms_geom_lon_isclose:
                        arcpy.AddError("feature: " + str(row[0]) +
                                       " Long DMS:" + str(row[2]) +
                                       " Long geometry:" + str(dd_to_dms(row[5][0].X)))

                # print geom vs DD
                if parameters[4].value:
                    if not dd_geom_lat_isclose:
                        arcpy.AddError("feature: " + str(row[0]) +
                                       " Lat DD:" + str(row[3]) +
                                       " Lat geometry:" + str(row[5][0].Y))
                    if not dd_geom_lon_isclose:
                        arcpy.AddError("feature: " + str(row[0]) +
                                       " Long DD: " + str(row[4]) +
                                       " Long geometry:" + str(row[5][0].Y))

                # print DMS vs DD
                if parameters[7].value:
                    if not dms_dd_lat_isclose:
                        arcpy.AddError("feature: " + str(row[0]) +
                                       " Lat DMS:" + str(row[1]) +
                                       " Lat DD:" + str(dd_to_dms(row[3])))
                    if not dms_dd_long_isclose:
                        arcpy.AddError("feature: " + str(row[0]) +
                                       " Long DMS:" + str(row[2]) +
                                       " Long DD: " + str(dd_to_dms(row[4])))

                # write feature values to excel spreadsheet
                # TODO: write DD instead of whatever crap is written
                for i in range(len(row)):
                    if str(row[i]).startswith("<"):
                        ws.write(row_counter, i, row[i].WKT)
                    else:
                        ws.write(row_counter, i, str(row[i]))

                # write test outcomes to excel spreadsheet
                if parameters[1].value:
                    if not dms_geom_lat_isclose or not dms_geom_lon_isclose:
                        text = "FAIL"
                        style = red_style
                    else:
                        text = "PASS"
                        style = green_style
                    ws.write(row_counter, 6, text, style)
                if parameters[4].value:
                    if not dd_geom_lat_isclose or not dd_geom_lon_isclose:
                        text = "FAIL"
                        style = red_style
                    else:
                        text = "PASS"
                        style = green_style
                    ws.write(row_counter, 7, text, style)
                if parameters[7].value:
                    if not dms_dd_lat_isclose or not dms_dd_long_isclose:
                        text = "FAIL"
                        style = red_style
                    else:
                        text = "PASS"
                        style = green_style
                    ws.write(row_counter, 8, text, style)

            # save the excel workbook
            if parameters[8].value:
                from tempfile import mkstemp
                from os import startfile
                out_xls = mkstemp(suffix=".xls")[1]
                arcpy.AddMessage(out_xls)
                wb.save(out_xls)
                startfile(out_xls)
