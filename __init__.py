# -*- coding: utf-8 -*-
"""
/***************************************************************************
 FeatureElevation
                                 A QGIS plugin
 Fills in a feature numerical field with elevation using Google Elevation Api
                             -------------------
        begin                : 2017-01-28
        copyright            : (C) 2017 by Jorge Almerio
        email                : jorgealmerio@yahoo.com.br
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load FeatureElevation class from file FeatureElevation.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from FeatureElevationModule import FeatureElevation
    return FeatureElevation(iface)
