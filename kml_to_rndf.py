import sys
import getopt
import urllib2
import re
from pykml import parser
from pykml import helpers
from lxml import objectify
from lxml import etree

namespace = 'http://earth.google.com/kml/2.2'

def get_tree_from_url(url):
    fileobject = urllib2.urlopen(url)
    tree = parser.parse(fileobject)
    return tree.getroot()

def get_segment_data(placemark, wp_count=0, outFile=None):
    name = None
    points = []
    for elem in placemark.iterchildren():
        tag = helpers.separate_namespace(elem.tag)[1]
        if tag == 'name':
            name = re.sub('\s', '', elem.text)
        elif tag == 'LineString':
            for coordinate in re.split('\s+', elem.coordinates.text)[1:-1]:
                wp_loc = str.split(coordinate, ',')
                points.append(wp_loc[0:2])
    return name, points

def process_kml(kml_root, outFile=None):
    placemarks = kml_root.Document.findall('{'+namespace+'}Placemark')
    wp_count = 0
    segments = []
    for placemark in placemarks:
        segment = get_segment_data(placemark)
        if segment[1] == []:
            continue
        segments.append(segment)

    return segments

def get_rndf_lines(segments):
    output_lines = ["RNDF_name back_40_one_way_rndf.txt",
                    "num_segments " + str(len(segments)),
                    "num_zones 0",
                    "format_version 1",
                    "creation_date 5-Nov-2012",
                    ""
                    ]
    for idx, seg in enumerate(segments):
        seg_num = str(idx + 1)
        name, coords = seg
        lane_num = str(seg_num) + ".1"
        output_lines.extend(["",
                             "segment " + seg_num,
                             "name " + name,
                             "num_lanes 1",
                             "lane " + lane_num,
                             "num_waypoints " + str(len(seg[1]))
                             ])
        for wp_idx, coord in enumerate(coords):
            wp_num = lane_num + "." + str(wp_idx + 1)
            lon, lat = coord
            output_lines.append(wp_num + " " + lat + " " + lon)

        output_lines.extend(["end_lane",
                             "end_segment"
                             ])
    output_lines.append("end_file")
    return output_lines

        

def main(argv=None):
    if argv is None:
        argv = sys.argv

    url = argv[1]
    tree = get_tree_from_url(url)

    outFile = open('test.rndf', 'w')
    segments = process_kml(tree, outFile)
    rndf_lines = get_rndf_lines(segments)
    outFile.write('\n'.join(rndf_lines))
    outFile.close()


if __name__ == "__main__":
    sys.exit(main())
