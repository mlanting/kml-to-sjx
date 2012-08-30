import sys
import getopt
import urllib2
import re
from pykml import parser
from pykml import helpers
from lxml import objectify
from lxml import etree

namespace = 'http://earth.google.com/kml/2.2'
outFile = open('test.yaml', 'w')
defaultInitScript = "'// Refer to newly created entity with ''self''\n\
\n\
    logger.info(\"Created entity \" + self.name);\n\
\n\
'"

typeMap = {'Point':'waypoint', 'LineString':'route', 
           'RPGReport':'threat-rpg', 'RPG':'rpg',
           'SAFReport':'threat-saf', 'SAF':'saf',
           'IEDReport':'ied-undetonated', 'IED':'ied'
           }

def get_tree_from_url(url):
    fileobject = urllib2.urlopen(url)
    tree = parser.parse(fileobject)
    return tree.getroot()

def create_entity_element(name, prototype, location, force="friendly", visible=True, orientation=0.0, initScript=defaultInitScript, points=['[]']):
    #create_entity_element_debug(name, prototype, location, points=points)
    write_entity_element_yaml(name, prototype, location, points=points)
    return

def write_entity_element_yaml(name, prototype, location, force="friendly", visible='false', orientation=0.0, initScript=defaultInitScript, points=[]):
    output_lines = ['',
                    '- alt: ' + location[2],
                    '  force: ' + force,
                    '  heading: ' + '0.0',
                    '  initScript: ' + initScript,
                    '  lat: ' + location[1],
                    '  lng: ' + location[0],
                    '  name: ' + name,
                    '  pitch: ' + '0.0',
                    '  points: ' + '\n  - '.join(points),
                    '  prototype: ' + prototype,
                    '  roll: ' + '0.0',
                    '  visible: ' + visible]
    outFile.write('\n'.join(output_lines))
    return
    

def create_entity_element_debug(name, prototype, location, force="friendly", visible=True, orientation=0.0, initScript=defaultInitScript, points=[]):
    print 'name: ' + name
    print 'prototype: ' + prototype
    print 'lng: ' + location[0]
    print 'lat: ' + location[1]
    print 'alt: ' + location[2]
    print 'points:' + str(points)
    return

def parse_name(name):
    name_parts = re.split('\s+', name)
    print 'type: ' + name_parts[1] + name_parts[2]
    

def convert_placemark(placemark, wp_count=0):
    name = None
    prototype = None
    location = None
    points = []
    for elem in placemark.iterchildren():
        tag = helpers.separate_namespace(elem.tag)[1]

        if tag == 'name':
            name = elem.text
        elif tag == 'Point':
            prototype = 'waypoint'
            location = str.split(elem.coordinates.text, ',')
            points.append('[]')
        elif tag == 'LineString':
            prototype = 'route'
            location = ['0', '0', '0']
            points.append('')
            for coordinate in re.split('\s+', elem.coordinates.text)[1:-1]:
                wp_name = 'wp'+str(wp_count)
                wp_loc = str.split(coordinate, ',')
                create_entity_element(wp_name, 'waypoint', wp_loc)
                wp_count += 1
                points.append(wp_name)

    create_entity_element(name, prototype, location, points=points)

    return wp_count

def process_kml(kml_root):
    placemarks = kml_root.Document.findall('{'+namespace+'}Placemark')
    wp_count = 0
    for placemark in placemarks:
        wp_count = convert_placemark(placemark, wp_count)

    outFile.close()
    return

def main(argv=None):
    if argv is None:
        argv = sys.argv

    url = argv[1]
    tree = get_tree_from_url(url)
    process_kml(tree)


if __name__ == "__main__":
    sys.exit(main())
