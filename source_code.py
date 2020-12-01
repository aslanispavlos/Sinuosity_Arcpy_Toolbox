# -*- coding: utf-8 -*-
"""
Created during the period  October 14th - November 1st 

@author: pa6321as-s
""" 
#                                             .----------------------------.
#                                            ( what is my sinuosity? help! )
#                                            /`---------------------------`
###                           (o)(o)
##                          /     \      
##                         /       |
##                        /   \  * |
##          ________     /    /\__/
##  _      /        \   /    /
## / \    /  ____    \_/    /
##//\ \  /  /    \         /
##   \ \/  /      \       /
##    \___/        \_____/
"""
############################################################
# This script was created for the NGEN13 project.
############################################################
"""

######################################################
import arcpy
from arcpy.sa import * # Importing the Spatial Analyst module
import sys

####################################  
try:
    arcpy.env.overwriteOutput = True
    arcpy.CheckOutExtension("spatial")
    river_list = arcpy.GetParameterAsText(0).split(';')
    year_list = arcpy.GetParameterAsText(1).split(';')
    river_section_bool = arcpy.GetParameterAsText(2)
    sections = arcpy.GetParameterAsText(3)
    normalize_sin_bool = arcpy.GetParameterAsText(4)
    arcpy.env.workspace = arcpy.GetParameterAsText(5)
    wr = str(arcpy.env.workspace)   
    
    # Catch the error of the years in the names of the input shapefiles, being different than the input in the year list.

    found = 0                                               # How many elements of the year_list were found in the river_list
    for i in range(0,len(year_list)):
        for j in range(0,len(river_list)):
            if year_list[i] in river_list[j]:
                found += 1
    if found == len(year_list):                             # If all the elements of the year list  were found in the river list
        pass
    else:
        arcpy.AddError("The years that were used as input in the year of input features are not the same as the ones in the shapefile names ... Please check the input Shapefile Years, and the year list that were used as input ...")
        sys.exit(0)                                         # If not there was an error in the inputs... - EXIT
    ########################################################################################################################################
    def getSinuosity(shape):
        ## This functions calculates the sinuosity of a polyline.
        ## Needs as an input a polyline shapefile. 
        ## And a list of the years that the shapefiles are refering to.
        ## Also divides the line into section in order to calculate the sinuosity per section.
        
        #############################################
        # Catching possible Errors - Error handling.
        #############################################
        
        # Catch the error of using an empty shapefile (i.e. with no features in it)
        f_count = arcpy.GetCount_management(shape)
        if int(f_count[0]) > 0:
            arcpy.AddMessage("The input {0} has {1} features".format(shape.split("\\")[-1], f_count))
        else:
            arcpy.AddError('The input {}  has no features the execution of the script will fail ... Please check the input shapefiles ...'.format(shape.split("\\")[-1]))        
            sys.exit(0)
            
                 
        # Catch the error of having an unknown spatial reference for the input data.
        spatial_ref = arcpy.Describe(shape).spatialReference

        if spatial_ref.name != "Unknown":
            arcpy.AddMessage("The spatial reference of {0} is {1}".format(shape.split("\\")[-1], spatial_ref.name))
        else:
            arcpy.AddError("Beware ... the used input {0} has Unknown spatial reference ... Please check the Spatial Reference of the input shapefiles ... The execution of the script will be terminated soon ..." .format(shape))
            sys.exit(0)
            
        # Catch the geometry Type error (of the input shapefiles not being polyline)
        desc = arcpy.Describe(shape)
        geometryType = desc.shapeType
        if  str(geometryType) == 'Polyline':
            pass
        else:
            arcpy.AddError('{}  is not a line/polyline ... Please check the input shapefiles ...'.format(shape.split("\\")[-1]))
            sys.exit(0)
            
        #####################
        # Calculate Sinuosity          
        #####################    
            
        arcpy.AddMessage("### Calculating sinuosity index for the whole river ###")   
        for year in year_list:                                                        # Go through all the different Years the user enter as input (stored in a list).
            if year in shape:                                                         # If the Year input connects to a shapefile input (i.e. the user did not put wrong Year).
                try:                   
                    if int(f_count[0]) > 1:                                                        # If the input consits of multiple features dissolve it to 1.
                        arcpy.AddMessage("{0} has {1} features and it will be dissolved into 1 feature ...".format(shape.split("\\")[-1], f_count))
                        shape_dissolve = r'river_dissolved.shp'                                    # Name of the shapefile for the dissolved river
                        arcpy.Dissolve_management(shape,shape_dissolve)                            # Perform dissolve 
                        shape = shape_dissolve                                                     # From now on the dissolved shape is going to be the variable shape.
                    arcpy.AddMessage("Adding Geometry field ...")
                    arcpy.AddGeometryAttributes_management(shape, "LENGTH", "METERS")              # Add a Geometry field to calculate the length of each feature.
                    arcpy.AddMessage("Adding field ...")
                    arcpy.AddField_management(shape, 'TOT_LENGTH', 'DOUBLE')                       # Add another field "TOT_LENGTH" to copy the values ofthe length field - fixing field names to avoid confusions.
                    arcpy.AddMessage("Calculating field ...")
                    arcpy.CalculateField_management(shape, "TOT_LENGTH","!LENGTH!" , "PYTHON")     # Actually copying the values of "LENGTH" to the new field added above. 
                    arcpy.AddMessage("Deleting field ...")
                    arcpy.DeleteField_management(shape, "LENGTH")                                  # Delete the geometry field that was just created.
                    arcpy.AddMessage("Calculating total length of the river ...")
                    cursor = arcpy.da.SearchCursor(shape,["TOT_LENGTH"])                           # Use a search cursor to go through the "TOT_LENGTH" of the input shapefile.
                    length = 0
                    for row in cursor:                                                             # For all the individual features / lines in a polyline.
                        length += row[0]                    
                    arcpy.AddMessage("Extracting the ending point of the river ...")
                    river_end_shp = r'end_' + str(year) + '.shp'                                   # Variable for the shapefile of the end point of the polyline.
                    arcpy.AddMessage("Extracting the starting point of the river ...")                   
                    river_start_shp = r'start_' + str(year) +'.shp'                                # Variable for the shapefile of the start point of the polyline.
                    arcpy.AddMessage("Feature Vertices to Points for the 'start' and 'end' vertices of the river ...")
                    arcpy.FeatureVerticesToPoints_management (shape, river_end_shp, "end")         # Convert the last-end vertex of the polyline (river) to point, output River_end
                    arcpy.FeatureVerticesToPoints_management (shape, river_start_shp, "start")     # Convert the first-start vertex of the polyline (river) to point, output River_start.
                    arcpy.AddMessage("Calculating straight distance between start and end vertices of the river ...")
                    distance_table = r'distance' + str(year) +'.dbf'
                    arcpy.PointDistance_analysis(river_end_shp,river_start_shp, distance_table,"") # Calculate the straight distance between start and end and save it to a table 
                    cursor = arcpy.da.SearchCursor(distance_table,"DISTANCE")                      # Use a search cursor to go through the distance collumn in the created distance table.
                    d=0                                                                            # Variable for straight distance - direct distance
                    for rows in cursor:                                                            # For the different rows of the distance collumn in the distance_table 
                        d = rows[0]                                                                # Add the different rows (the distance will always in the first row though)                  
                    arcpy.AddMessage("The straight distance between the starting and ending point is now computed and stored in the {}".format(distance_table))
                    if normalize_sin_bool == 'true':               
                        sinuosity = d / length                                                     # Defined as Length / d but reverse is used, Max possible sinuosity = 1 .
                    else: 
                        sinuosity = length / d                                                     # Normalized sinuosity index as used by ESRI toolbox.
                except:
                    arcpy.AddMessage(arcpy.GetMessages())

                arcpy.AddMessage("Adding field ...")
                arcpy.AddField_management(shape, 'sinuosity', 'DOUBLE')                            # Add a field in the river shapefile to store the sinuosity value
                arcpy.AddMessage("Calculating field ...")
                arcpy.CalculateField_management(shape,'sinuosity',sinuosity,'VB')                  # Calculate the sinuosity field - actually store the value in the table of the shapefile.                                                   
                ###############################
                ## Sinuosity per Section Part.
                ###############################
                if river_section_bool == 'true':                                                   # This condition is satisfied if the user selected to also calculate the Sinuosity Index per section.
                    
                    arcpy.AddMessage("### Calculating sinuosity index for different parts of the river ####")
                    arcpy.AddMessage("You have selected {0} sections ".format(sections))           # Need to move in the IF for the section statement
                    arcpy.AddMessage("Creating new shapefiles ...")
                    points_along_shape_shp = r'points_along_shape_' + str(year) + '.shp'           # Variable for the shapefile of the points along the river line.  
                    river_section_shp = 'river_sections_year_' + str(year) + '.shp'                # Variable for the shapefile of the river divided into sections.
                    arcpy.AddMessage("Calculating the length of sections in % of total length ...")
                    per = 100 / int(sections)                                                      # Calculate the percentage of each section based on the Number of Sections that the user asked with his input.
                    arcpy.AddMessage("The percentage of the total length for each section is :{}".format(per))
                    arcpy.AddMessage("Generating points along the river line ...")
                    arcpy.GeneratePointsAlongLines_management(shape, points_along_shape_shp, "PERCENTAGE", Percentage = per,Include_End_Points='NO_END_POINTS')     # Generate points along the based on the above calculate percentage.
                    ##Added to delete the last point of the points along lines.
                    points_temp = 'points_along_shape'+ str(year) + 'filtered.shp'                                           # Temporary shapefile used to delete the point the the edge of the line from the points along the line.
                    arcpy.MakeFeatureLayer_management(points_along_shape_shp, points_temp)
                    sel_exp = "\"FID\"=" +str(int(sections) - 1)                                                             # The last one will have FID the number of sections -1
                    arcpy.SelectLayerByAttribute_management(points_temp,"NEW_SELECTION",sel_exp)
                    if int(arcpy.GetCount_management(points_temp)[0]) > 0:                                                   # If there are any features satisfying this condition - Will be!
                        arcpy.DeleteFeatures_management(points_temp)                                                         # Delete them.
                    
                    ##
                    
                    arcpy.AddMessage("Spliting line on points ...")
                    arcpy.SplitLineAtPoint_management(shape, points_along_shape_shp, river_section_shp,"2000 Meters")                                               # Splitting the line into sections by using the above generate points.
                    arcpy.AddMessage("Adding Geometry field ...")
                    arcpy.AddGeometryAttributes_management(river_section_shp, "LENGTH", "METERS")                                                                   # Get the length of each section
                    arcpy.AddMessage("Adding field ...")
                    arcpy.AddField_management(river_section_shp, 'SEC_LENGTH', 'DOUBLE')                                                                            # Store the length in a new field "SEC_LENGTH" to be more clear - avoid confusion.
                    arcpy.AddMessage("Calculating field ...")
                    arcpy.CalculateField_management(river_section_shp, "SEC_LENGTH","!LENGTH!" , "PYTHON")
                    arcpy.AddMessage("Deleting field ...")                                                                                                          # Delete the "LENGTH" field in the same logic.
                    arcpy.DeleteField_management(river_section_shp, "LENGTH")
                    arcpy.AddMessage("The calculation of the length of each section was successful, the values are stored in the field ""\"SEC_LENGTH\""" ")                       
                    river_section_shp_lvl2 = 'river_sections_year_'+ str(year)+'lvl2' + '.shp'                   # Variable for the shapefile of the river sections that will be used to be sure that the script will delete all the sections  
                                                                                                                 # that are substantially 'small' because in such a case the sinuosity values of that sections will be missleading
                    arcpy.CopyFeatures_management(river_section_shp, river_section_shp_lvl2)
                    temp_sec_len_l = []                                                                          # Create an empty list that will store all the length values of the different sections.
                    cursor = arcpy.da.SearchCursor(river_section_shp_lvl2, "SEC_LENGTH")                         # Use a search cursor to go through the section length field.
                    for row in cursor:
                        temp_sec_len_l.append(int(row[0]))                                                       # Populate/Append each value of the field to the list we just created.
                    minimum_section_length = min(temp_sec_len_l)                                                 # Find the minimum length per section.
                    mean_section_length = sum(temp_sec_len_l)/len(temp_sec_len_l)                                # And find the average length per section.
                    arcpy.AddMessage("Minimum section length :{}".format(minimum_section_length))
                    arcpy.AddMessage("Average section length :{}".format(mean_section_length))
                    arcpy.AddMessage("Deleting the substantially small sections ...") 
                    temp = 'river_sections_year_'+ str(year)+'lvl3' + '.shp'                                     # Temporary shapefile used to delete the 'small' sections
                    arcpy.MakeFeatureLayer_management(river_section_shp_lvl2, temp)
                    delete_thres = 0.35                                                                          # Threshold of deletion (Small section) is defined as 0.35 of the average length of the sections 
                    exp_sec_len = "\"SEC_LENGTH\" <" + str(delete_thres * mean_section_length)
                    arcpy.SelectLayerByAttribute_management(temp,"NEW_SELECTION",exp_sec_len)                    # Select the features by attributes based on the above threshold/expression
                    if int(arcpy.GetCount_management(temp)[0]) > 0:                                              # If there are any features satisfying this condition - 
                        arcpy.AddWarning("{} of the generated sections were substantially smaller than the average section length, and they are being deleted ...".format(int(arcpy.GetCount_management(temp)[0])))
                        arcpy.DeleteFeatures_management(temp)                                                    # Delete them                    
                    ######
                    arcpy.AddMessage("Adding field ...")
                    arcpy.AddField_management(river_section_shp_lvl2,"startx","DOUBLE")                          # Field that will store the X coordinate of the starting point of each section.
                    arcpy.AddMessage("Adding field ...")
                    arcpy.AddField_management (river_section_shp_lvl2,"starty","DOUBLE")                         # Field that will store the Y coordinate of the starting point of each section.
                    arcpy.AddMessage("Adding field ...")
                    arcpy.AddField_management (river_section_shp_lvl2,"endx","DOUBLE")                           # Field that will store the X coordinate of the ending point of each section.
                    arcpy.AddField_management (river_section_shp_lvl2,"endy","DOUBLE")                           # Field that will store the Y coordinate of the ending point of each section.
                    arcpy.AddMessage("Adding field ...")
                    arcpy.AddField_management(river_section_shp_lvl2,'dirdis','DOUBLE')                          # Field that will store the direct distance for each section of the river from starting to ending vertex.
                    arcpy.AddMessage("Adding field ...")
                    arcpy.AddField_management (river_section_shp_lvl2,"sec_sin","DOUBLE")                        # Field that will store the sinuosity of EACH Section.
                    
                    #Expressions for the calculations of the new fields.                                         # Create the expressions in order to populate the fields that were just created above.
                    exp_start_X = "!Shape!.positionAlongLine(0.0,True).firstPoint.X"                             # expression for starting X
                    exp_start_Y = "!Shape!.positionAlongLine(0.0,True).firstPoint.Y"                             # expression for starting Y
                    exp_end_X = "!Shape!.positionAlongLine(1.0,True).firstPoint.X"                               # expression for ending X
                    exp_end_Y =  "!Shape!.positionAlongLine(1.0,True).firstPoint.Y"                              # expression for ending Y
                    arcpy.AddMessage("Calculating field ...")                                                    # Finally
                    arcpy.CalculateField_management(river_section_shp_lvl2, "startx", exp_start_X, "PYTHON")     # Populate/Calculate the starting X-coordinate of each section.
                    arcpy.AddMessage("Calculating field ...")
                    arcpy.CalculateField_management(river_section_shp_lvl2, "starty", exp_start_Y, "PYTHON")     # Populate/Calculate the starting X-coordinate of each section.
                    arcpy.AddMessage("Calculating field ...")
                    arcpy.CalculateField_management(river_section_shp_lvl2, "endx", exp_end_X, "PYTHON")         # Populate/Calculate the starting X-coordinate of each section
                    arcpy.AddMessage("Calculating field ...")
                    arcpy.CalculateField_management(river_section_shp_lvl2, "endy", exp_end_Y, "PYTHON")         # Populate/Calculate the starting X-coordinate of each section
                                                                                                                 # Based on the above (Xstart-Xend,Ystart,Yend) and using
                    dd_exp = "math.sqrt((!startx!-!endx!)**2+(!starty!-!endy!)**2)"                              # The pythagoreum we can now get straight distance.
                    arcpy.AddMessage("Calculating field ...")
                    arcpy.CalculateField_management(river_section_shp_lvl2,"dirdis",dd_exp,"PYTHON")             # Populate the field based on the pythagoreum expression for each section.
                    
                    if normalize_sin_bool == 'true':               
                        sin_exp= "!dirdis!/!SEC_LENGTH!"                                                         # Defined as Length / d but reverse is used, Max possible sinuosity = 1 .
                    else:                                                                                        # Expression for Sinuosity Formula (direct distance / Length).
                        sin_exp= "!SEC_LENGTH!/!dirdis!"
                    arcpy.AddMessage("Calculating field ...")                                                    
                    arcpy.CalculateField_management(river_section_shp_lvl2,"sec_sin",sin_exp,"PYTHON")           # Populate/Calculate the sections sinuosity field based on the sinuosity expression for each section.
                    arcpy.AddMessage("The calculation of the sinuosity per section was successful, the values are stored in a field named ""\"sec_sin\""" ")
    
    # Execute the function for every input shapefile from the user!                
    for river in river_list:    
        getSinuosity(river)
                
except:
    arcpy.AddError("The execution FAILED! ... Hopefully there is a more explanatory error message above ... Please try again!")
    arcpy.AddMessage(arcpy.GetMessages())    
    
