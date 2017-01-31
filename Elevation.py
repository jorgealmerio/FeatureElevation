# -*- coding: utf-8 -*-#
# This file is part of the QGIS Feature Elevation Plugin
#
# Elevation.py - load Elevation class from file Elevation.py
#
# Copyright 2010, 2013, 2014 Jorge Almerio <jorgealmerio@yahoo.com.br>
#
# The QGIS Feature Elevation plugin is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2, or (at your option) any later version.
#
# The QGIS Feature Elevation plugin is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with program; see the file COPYING. If not,
# write to the Free Software Foundation, Inc., 59 Temple Place
# - Suite 330, Boston, MA 02111-1307, USA.
#
# The QGIS Python bindings are required to run this file
# 
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import * 
from PyQt4.QtGui import *
from qgis.core import *
from qgis.utils import *

import sys, os, httplib, json, tempfile, urllib

# GeoCoding Utils
#from Utils import *



class elevationClass:
    def __init__(self):
        # Save reference to the QGIS interface
        self.iface = iface
        #self.canvas = iface.mapCanvas()
        # store layer id
        self.layerid = ''

    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('elevationClass', message)

    # Obtain elevation
    def LayerFeat_enum(self, layer, fldElev, fldRes):
        chk = self.check_settings()
        progressMessageBar = iface.messageBar().createMessage(self.tr("Getting Elevation Data..."))
        progress = QProgressBar()
        progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        iface.messageBar().pushWidget(progressMessageBar, iface.messageBar().INFO)
        if len(chk) :
            QMessageBox.information(self.iface.mainWindow(), self.tr("Feature Elevation plugin error"), chk)
            return
        onlySel=False
        if layer.selectedFeatureCount()==0:
            feicoes=layer.getFeatures()
        else:
            resp=QMessageBox.question(None,'Feature Elevation',self.tr('Get elevation only for selected features?'),
                                      QMessageBox.Yes, QMessageBox.No)
            if resp==QMessageBox.Yes:
                onlySel=True
                feicoes=layer.selectedFeatures()
            else:
                feicoes=layer.getFeatures()

        #elevID=dp.fieldNameIndex(fldElev)
        #resID=dp.fieldNameIndex(fldRes)
        i=0
        for feat in feicoes:
            i+=1
        #import time
        progress.setMaximum(i)
        progressMessageBar.layout().addWidget(progress)
        i=0
        if onlySel:
            feicoes=layer.selectedFeatures()
        else:
            feicoes=layer.getFeatures()
        layer.startEditing()
        for feat in feicoes:
            progress.setValue(i)
            QApplication.processEvents()
            #time.sleep(1)
            pto=feat.geometry().asPoint()
            elev,res=self.get_elev(pto)
            #elev,res=i*10,333
            if fldElev:
                feat[fldElev]=elev
            if fldRes:
                feat[fldRes]=res
            layer.updateFeature(feat)
            i+=1
        iface.messageBar().clearWidgets()
#         dp=layer.dataProvider()
#         elevID=dp.fieldNameIndex(fldElev)
#         resID=dp.fieldNameIndex(fldRes)
#         attrs ={}
#         for feat in layer.getFeatures():
#             pto=feat.geometry().asPoint()
#             elev,res=self.get_elev(pto)
#             print elev, res
#             if elevID>=0:
#                 attrs[elevID]=elev
#             if resID>=0:
#                 attrs[resID]=res
#             dp.changeAttributeValues({feat.id(): attrs})

    def get_elev(self, point) :
        epsg4326 = QgsCoordinateReferenceSystem(4326, QgsCoordinateReferenceSystem.EpsgCrsId)
        self.reprojectgeographic = QgsCoordinateTransform(self.iface.mapCanvas().mapRenderer().destinationCrs(), epsg4326)
        pt = self.reprojectgeographic.transform(point)
        conn = httplib.HTTPConnection("maps.googleapis.com")
        #QgsMessageLog.instance().logMessage( "http://maps.googleapis.com/maps/api/elevation/json?locations=" + str(pt[1])+","+str(pt[0])+"&sensor=false", "Elevation")
        conn.request("GET", "/maps/api/elevation/json?locations=" + str(pt[1])+","+str(pt[0])+"&sensor=false")
        response = conn.getresponse()                
        jsonresult = response.read()
        try:
            results = json.loads(jsonresult).get('results')
            if 0 < len(results):
                elevation = results[0].get('elevation')
                resolution = results[0].get('resolution')
                # save point
                return elevation, resolution
            else:
                QMessageBox.warning(self.iface.mainWindow(), 'Elevation', 'HTTP GET Request failed.', QMessageBox.Ok, QMessageBox.Ok)
        except ValueError, e:
            QMessageBox.warning(self.iface.mainWindow(), 'Elevation', 'JSON decode failed: '+str(jsonresult), QMessageBox.Ok, QMessageBox.Ok)
 
    # save point to file, point is in project's crs
    def save_point(self, point, elevation):
        # create and add the point layer if not exists or not set
        if not QgsMapLayerRegistry.instance().mapLayer(self.layerid) :
            # create layer with same CRS as project
            self.layer = QgsVectorLayer("Point?crs=epsg:4326", "Elevation Plugin Results", "memory")
            self.provider = self.layer.dataProvider()

            # add fields
            self.provider.addAttributes( [QgsField("elevation", QVariant.Double)] )
            self.layer.updateFields()

            # Labels on
            label = self.layer.label()
            label.setLabelField(QgsLabel.Text, 0) 
            self.layer.enableLabels(True)

            # add layer if not already
            QgsMapLayerRegistry.instance().addMapLayer(self.layer)

            # store layer id
            self.layerid = QgsMapLayerRegistry.instance().mapLayers().keys()[-1]

        # add a feature
        fet = QgsFeature()
        fet.initAttributes(1)
        fet.setGeometry(QgsGeometry.fromPoint(self.reprojectgeographic.transform(point)))
        fet.setAttribute(0, elevation)
        self.provider.addFeatures( [ fet ] )

        # update layer's extent when new features have been added
        # because change of extent in provider is not propagated to the layer
        self.layer.updateExtents()

        self.canvas.refresh()

    # check project settings before obtaining elevations
    # return an error string
    def check_settings (self) :
        p = QgsProject.instance()
        error = ''
        proj4string = self.iface.mapCanvas().mapRenderer().destinationCrs().toProj4()
        return error

if __name__ == "__main__":
    pass
    
