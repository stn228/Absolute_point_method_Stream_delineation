from qgis.core import QgsProcessing
import time
import processing
import math

#Author: Stijn Ticheloven

#This script delineates single streams from an arbitrary starting point
#towards the lowest point in the input dataset.
#In the first section, some parameters have te be set up.
#Then, the search angle is defined to implement in the field calculator.
#A point is selected and the expression for the field calculator is executed to select
#the lowest point within the specified search radius.
#If the z-value of strarting point is lower than the end point,
#the extended search radius will be applied.
#This process is iterated until the model is at the lowest point in the dataset.


#########################
### SET UP PARAMETERS ###
#########################

result = 'C:/Users/stijn/OneDrive/Documents/GIMA/Scriptie/Analysis/stream/stream_delineation.shp'
#Layer name of the point dataset.
#This should be a point-vector layer with points with a Z-attributes
layername = 'points'
#Default search radius (m)
search_radius = 3
#Extended search radius (m)
extended_radius = 5
#Maximum allowed course change in degrees
course_Change = 88
#Selected starting point
id_startPoint = 352894
#set the Z-value of the end point (the end point of the algorithm)
lowest_point = 160
#temporary file directory
fn = "C:/Users/stijn/OneDrive/Documents/GIMA/Scriptie/Analysis/stream/bin/polysegment.shp"


########################
###Start of Algorithm###
########################

#get start time
start_time = time.time()

#select starting point
activate = QgsProject.instance().mapLayersByName(layername)[0]
iface.setActiveLayer(activate)
lyr = iface.activeLayer()

lyr.selectByExpression(f"\"id\" = {id_startPoint} ") 
        
#Definition LowestNeighbour calculates the lowest neighbour within the default search radius
def lowestNeighbour():
   #set active layer
    layer = iface.activeLayer()
    #create new column for the table in the input point dataset
    pv = layer.dataProvider()
    pv.addAttributes([QgsField('low_neigh', QVariant.Int)])

    layer.updateFields()
    
    features = lyr.selectedFeatures()
    for feat in features:
        attrs = feat.attributes()

    #Define the maximum allowed course change with the minimum and maximum angle

    #Since the maximum allowed course change is based on two points, it cannot be
    #calculated for the starting point. Thus, the starting point is 0 - 360 degrees allowed
    #course change
    if attrs[2] == id_startPoint:
        r1=0
        r2=360
    #atan2 uses the difference between point end_point and start_point as input to calculate the direction
    else:
        y =(end_y - start_y)
        x = (end_x-start_x)
        
        angle = math.degrees(math.atan2(x,y))

        #The search radius is just not perpendicular to the direction (thus, 88 degrees)
        r1 = angle - course_Change
        r2 = angle + course_Change
        
        #Note that atan2 returns positive and negative angles
        #This statement is done to convert the negative angles to positives
        #It also is used if it exceeds 360 or 0 because of the previous statement
        if r1 > 360:
            r1 = r1 -360
        elif r1 < 0:
            r1 = r1 + 360   
        if r2 > 360:
            r2 = r2 -360
        elif r2 < 0:
            r2= r2 + 360

    global r1a
    r1a = r1
    global r2a
    r2a=r2

    #Field calculator
    #This expression calculates the value for the new column 'low_neigh'
    #The expression selects the point with the lowest z-value within the specified
    #search radius, concerning the above calculated maximum allowed course change 
    if (r2 < (2*course_Change)):
        expression1 = QgsExpression(f'''array_to_string(array_slice(array_remove_all(aggregate(layer:= '{layername}',aggregate:='array_agg',\
        expression:="Id",concatenator:=',',filter:=distance($geometry,\
        geometry(@parent)) < {search_radius} and (angle_at_vertex(make_line(geometry(@parent),\
        $geometry), vertex:=1) >= {r1} or angle_at_vertex(make_line(geometry(@parent),\
        $geometry), vertex:=1) <= {r2}),order_by:=z($geometry)), "Id"), 0,0))''')
    else:
        expression1 = QgsExpression(f'''array_to_string(array_slice(array_remove_all(aggregate(layer:= '{layername}',aggregate:='array_agg',\
        expression:="Id",concatenator:=',',filter:=distance($geometry,\
        geometry(@parent)) < {search_radius} and (angle_at_vertex(make_line(geometry(@parent),\
        $geometry), vertex:=1) >= {r1} and angle_at_vertex(make_line(geometry(@parent),\
        $geometry), vertex:=1) <= {r2}),order_by:=z($geometry)), "Id"), 0,0))''')
   
 
    
    #give the context for where this expression occurs
    context = QgsExpressionContext()
    context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(layer))
    
    #only update the selected features
    features1 = layer.selectedFeatures()
    #Update features
    with edit(layer):
        for f in features1:
            context.setFeature(f)
            f['low_neigh'] = expression1.evaluate(context)
            layer.updateFeature(f)

#This definition uses the bigger specified search radius
def biggerSearchRadius():
    #set active layer
    layer = iface.activeLayer()
    #create new column for the table in the input point dataset
    pv = layer.dataProvider()
    pv.addAttributes([QgsField('low_neigh1', QVariant.Int)])

    layer.updateFields()

    features = lyr.selectedFeatures()
    for feat in features:
        attrs = feat.attributes()

    #Define the maximum allowed course change with the minimum and maximum angle

    #Since the maximum allowed course change is based on two points, it cannot be
    #calculated for the starting point. Thus, the starting point is 0 - 360 degrees allowed
    #course change
    if attrs[2] == id_startPoint:
        r1=0
        r2=360
    #atan2 uses the difference between point end_point and start_point as input to calculate the direction
    else:
       
        print(r1a, r2a)

    #Field calculator
    #This expression calculates the value for the new column 'low_neigh'
    #The expression selects the point with the lowest z-value within the specified
    #search radius, concerning the above calculated maximum allowed course change

    if r2a<(2*course_Change):
        expression1 = QgsExpression(f'''array_to_string(array_slice(array_remove_all(aggregate(layer:= '{layername}',aggregate:='array_agg',\
        expression:="Id",concatenator:=',',filter:=distance($geometry,\
        geometry(@parent)) < {extended_radius} and (angle_at_vertex(make_line(geometry(@parent),\
        $geometry), vertex:=1) >= {r1a} or angle_at_vertex(make_line(geometry(@parent),\
        $geometry), vertex:=1) <= {r2a}),order_by:=z($geometry)), "Id"), 0,0))''')
 
    else:
        expression1 = QgsExpression(f'''array_to_string(array_slice(array_remove_all(aggregate(layer:= '{layername}',aggregate:='array_agg',\
    expression:="Id",concatenator:=',',filter:=distance($geometry,\
    geometry(@parent)) < {extended_radius} and (angle_at_vertex(make_line(geometry(@parent),\
    $geometry), vertex:=1) >= {r1a} and angle_at_vertex(make_line(geometry(@parent),\
    $geometry), vertex:=1) <= {r2a}),order_by:=z($geometry)), "Id"), 0,0))''')
    
    #give the context for where this expression occurs
    context = QgsExpressionContext()
    context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(layer))
    
    #only update the selected features
    features1 = layer.selectedFeatures()
    #Update Feature
    with edit(layer):
        for f in features1:
            context.setFeature(f)
            f['low_neigh1'] = expression1.evaluate(context)
            layer.updateFeature(f)
def createStream():
    #set active layer for the points
    #The origin point of the stream segment is selected at this point
    activate = QgsProject.instance().mapLayersByName(f'{layername}')[0]
    iface.setActiveLayer(activate)
    #define lowest nieghbour for selected point
    lowestNeighbour()
    #column attributes of the input layer
    features = lyr.selectedFeatures()
    for feat in features:
        attrs = feat.attributes()

    #define old Z value (to examine if this value is higher or lower than the new Z)
    z_old = float(attrs[7])
    
    #define starting point (that are the x, y values of the currently selected point)
    global start_x
    start_x = attrs[5] #column with X coordinate
    global start_y
    start_y = attrs[6] #column with Y coordinate
    #define qgsPoint
    # start = feat.geometry().centroid.x
    start = QgsPoint(start_x, start_y)
        
    #identify, select and define adjacent id with lowest elevation
    #The new selection is based on the calculated lowest neighbour
    new_selection = int(attrs[8]) #column with id of lowest neighbour

    #define the id of the old selection to reselect, if the extended search radius must be calculated
    iface.activeLayer()
    global old_selection
    old_selection = int(attrs[2]) #column with id
    #remove current selection
    lyr.removeSelection()

    #select new point with lowest elevation
    lyr.selectByExpression(f'"id" = {new_selection}')

    features = lyr.selectedFeatures()
    for feat in features:
        attrs = feat.attributes()

    #define new Z value
    z_new = float(attrs[4])
    
    #if z is not lower, extend search radius
    if z_new > z_old:
        #remove selection since the extended search radius is applied
        lyr.removeSelection()
        features = lyr.selectedFeatures()
        for feat in features:
            attrs = feat.attributes()
        #The original point is selected
        lyr.selectByExpression(f'"id" = {old_selection}')
        #the lowest point with z-value is identified within an extended search radius
        biggerSearchRadius()
        features = lyr.selectedFeatures()
        for feat in features:
            attrs = feat.attributes()
        lyr.selectByExpression(f'"id" = {old_selection}')
        extended_selection = int(attrs[8])
        lyr.removeSelection()
        lyr.selectByExpression(f'"id" = {extended_selection}')
        #define the end point
        features = lyr.selectedFeatures()
        for feat in features:
            attrs = feat.attributes()
        global end_x
        end_x = attrs[5] #column with X coordinate
        global end_y
        end_y = attrs[6] #column with Y coordinate
        end = QgsPoint(end_x, end_y)
        #draw line segment
        layer = QgsVectorLayer('LineString?crs=EPSG:28992', 'line' , 'memory')
        prov = layer.dataProvider()
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPolyline([start,end]))
        prov.addFeatures([feat])

        QgsProject.instance().addMapLayer(layer)

        QgsVectorFileWriter.writeAsVectorFormat(layer,'', "UTF-8", layer.crs(), "ESRI Shapefile")
        
        print("Extended search radius at point", old_selection)
    else:
        #define the end point
        end_x = attrs[6] #column with X coordinate
        end_y = attrs[7] #column with Y coordinate
        end = QgsPoint(end_x, end_y)
        #draw line segment
        v_layer = QgsVectorLayer('LineString?crs=EPSG:28992', 'line' , 'memory')
        prov = v_layer.dataProvider()
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPolyline([start,end]))
        prov.addFeatures([feat])

        QgsProject.instance().addMapLayer(v_layer)

        QgsVectorFileWriter.writeAsVectorFormat(v_layer,'', "UTF-8", v_layer.crs(), "ESRI Shapefile")
              

#while the elevation is higher than the lowest value, iterate the stream creation
features = lyr.selectedFeatures()
for feat in features:
    attrs = feat.attributes()
while float(attrs[4]) > lowest_point
    features = lyr.selectedFeatures()
    for feat in features:
        attrs = feat.attributes()
    createStream()

#merge and delete lines
listLayers = QgsProject.instance().mapLayersByName('line')
print(listLayers)
processing.runAndLoadResults("native:mergevectorlayers", 
                             {'LAYERS':listLayers,
                             'CRS':28992,
                             'OUTPUT': result})

lines_list = QgsProject.instance().mapLayersByName('line')[0:]
print(len(lines_list))
while len(lines_list) > 0:
    remove_layers = QgsProject.instance().mapLayersByName('line')[0]
    QgsProject.instance().removeMapLayer(remove_layers)
    lines_list = QgsProject.instance().mapLayersByName('line')[0:]

#print run time
print("--- %s seconds ---" % (time.time() - start_time))
