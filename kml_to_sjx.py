import sys
import getopt
import urllib2
import re
from pykml import parser
from pykml import helpers
from lxml import objectify
from lxml import etree

namespace = 'http://earth.google.com/kml/2.2'
scriptTemplate = "'// Refer to newly created entity with ''self''\n\
\n\
    logger.info(\"Created entity \" + self.name);\n\
    {0}\n\
'"
defaultScript = scriptTemplate.format('')
reportScriptTemplate = scriptTemplate.format('sumet.createReport({0});')
entityScriptTemplate = scriptTemplate.format('sumet.createEntity({0});')


#this is mostly just here for documentation at this point
typeMap = {'Point':'waypoint', 'LineString':'route', 
           'RPGReport':'threat-rpg', 'RPG':'rpg',
           'SAFReport':'threat-saf', 'SAF':'saf',
           'IEDReport':'ied-undetonated', 'IED':'ied'
           }

def get_tree_from_url(url):
    fileobject = urllib2.urlopen(url)
    tree = parser.parse(fileobject)
    return tree.getroot()

def create_entity_element(name, prototype, location, force="friendly", visible='true', orientation=0.0, initScript=defaultScript, points=['[]'], outFile=None):
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
    if prototype == 'script':
        outFile = open(name + '.yaml', 'w')
        outFile.write('events:\n')
        outFile.write('\n'.join(output_lines))
        outFile.close()
    else:
        outFile.write('\n'.join(output_lines))
    return

# Future version using a data object to hold the data rather than passing all the parameters in separately.
# Not yet used.
def write_element(elem):
    output_lines = ['',
                    '- alt: ' + elem.alt,
                    '  force: ' + elem.force,
                    '  heading: ' + '0.0',
                    '  initScript: ' + elem.initScript,
                    '  lat: ' + elem.lat,
                    '  lng: ' + elem.lng,
                    '  name: ' + elem.name,
                    '  pitch: ' + '0.0',
                    '  points: ' + '\n  - '.join(elem.points),
                    '  prototype: ' + elem.prototype,
                    '  roll: ' + '0.0',
                    '  visible: ' + elem.visible]
    if prototype == 'script':
        outFile = open(name + '.yaml', 'w')
        outFile.write('events:\n')
        outFile.write('\n'.join(output_lines))
        outFile.close()
    else:
        outFile.write('\n'.join(output_lines))
    return


def parse_name(name):
    name_parts = re.split(':?\s+', name)
    ret_name = '-'.join(name_parts)
    prototype = 'unknown'
    script = defaultScript

    while len(name_parts) < 3:
        name_parts.append('n/a')

    (obj_name, obj_type1, obj_type2) = name_parts[:3]
    
    if obj_type1 == 'IED':
        if obj_type2 == 'Report':
            prototype = 'script'
            script = reportScriptTemplate.format('"ied-undetonated", null, 0')
        else:
            prototype = 'script'
            script = entityScriptTemplate.format('"ied", 0')
    elif obj_type1 == 'RPG':
        if obj_type2 == 'Report':
            prototype = 'script'
            script = reportScriptTemplate.format('"threat-rpg", null, 0')
        else:
            prototype = 'script'
            script = entityScriptTemplate.format('"rpg", 0')
    elif obj_type1 == 'SAF':
        if obj_type2 == 'Report':
            prototype = 'script'
            script = reportScriptTemplate.format('"threat-saf", null, 0')
        else:
            prototype = 'script'
            script = entityScriptTemplate.format('"saf", 0')
    elif obj_type1 == 'Traffic':
        if obj_type2 == 'Report':
            prototype = 'script'
            script = reportScriptTemplate.format('"traffic-heavy", null, 0')
        else:
            prototype = 'script'
            script = entityScriptTemplate.format('"automobile", 0')
    elif obj_type1 == 'Obstacle' or obj_type1 == 'Obstacles' or obj_type1 == 'Blockage':
        if obj_type2 == 'Report':
            prototype = 'script'
            script = reportScriptTemplate.format('"obstacle-report", null, 0')
        else:
            prototype = 'script'
            script = entityScriptTemplate.format('"obstacle", 0')
    elif obj_type1 == 'Bridge-Out':
        if obj_type2 == 'Report':
            prototype = 'script'
            script = reportScriptTemplate.format('"bridge-disabled", null, 0')
        else:
            prototype = 'script'
            script = entityScriptTemplate.format('"obstacle", 0')
    else:
        if obj_name == 'Line' or obj_type1 == 'Route':
            prototype = 'route'
        else:
            prototype = 'waypoint'

    return ret_name, prototype, script
    

def convert_placemark(placemark, wp_count=0, outFile=None):
    name = None
    prototype = None
    location = None
    points = []
    for elem in placemark.iterchildren():
        tag = helpers.separate_namespace(elem.tag)[1]

        if tag == 'name':
            name, prototype, script = parse_name(elem.text)
        elif tag == 'Point':
            location = str.split(elem.coordinates.text, ',')
            points.append('[]')
        elif tag == 'LineString':
            location = ['0', '0', '0']
            points.append('')
            for coordinate in re.split('\s+', elem.coordinates.text)[1:-1]:
                wp_name = 'wp'+str(wp_count)
                wp_loc = str.split(coordinate, ',')
                create_entity_element(wp_name, 'waypoint', wp_loc, outFile=outFile)
                wp_count += 1
                points.append(wp_name)

    create_entity_element(name, prototype, location, points=points, initScript=script, outFile=outFile)

    return wp_count

def process_kml(kml_root, outFile=None):
    placemarks = kml_root.Document.findall('{'+namespace+'}Placemark')
    wp_count = 0
    for placemark in placemarks:
        wp_count = convert_placemark(placemark, wp_count, outFile)

    return

def main(argv=None):
    if argv is None:
        argv = sys.argv

    url = argv[1]
    outFileName = argv[2]
    tree = get_tree_from_url(url)

    outFile = open(outFileName+'.yaml', 'w')
    process_kml(tree, outFile)
    outFile.close()


if __name__ == "__main__":
    sys.exit(main())
