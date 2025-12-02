from lxml import etree
from typing import Optional, Dict, Any


def parse_comicinfo(xml_content: bytes) -> Dict[str, Any]:
    """Parse ComicInfo.xml and return structured data"""
    try:
        root = etree.fromstring(xml_content)

        # Helper to get text or None
        def get_text(element_name: str) -> Optional[str]:
            elem = root.find(element_name)
            return elem.text if elem is not None and elem.text else None

        return {
            # Basic info
            'series': get_text('Series'),
            'number': get_text('Number'),
            'volume': get_text('Volume'),
            'title': get_text('Title'),
            'summary': get_text('Summary'),
            'count': get_text('Count'),
            'age_rating': get_text('AgeRating'),
            'lang': get_text('LanguageISO'),

            # Date
            'year': get_text('Year'),
            'month': get_text('Month'),
            'day': get_text('Day'),

            # Credits
            'writer': get_text('Writer'),
            'penciller': get_text('Penciller'),
            'inker': get_text('Inker'),
            'colorist': get_text('Colorist'),
            'letterer': get_text('Letterer'),
            'cover_artist': get_text('CoverArtist'),
            'editor': get_text('Editor'),

            # Publishing
            'publisher': get_text('Publisher'),
            'imprint': get_text('Imprint'),
            'format': get_text('Format'),
            'series_group': get_text('SeriesGroup'),

            # Technical
            'page_count': get_text('PageCount'),
            'scan_information': get_text('ScanInformation'),

            # Tags (these come as comma-separated in the XML)
            'characters': get_text('Characters'),
            'teams': get_text('Teams'),
            'locations': get_text('Locations'),
            'genre': get_text('Genre'),

            # Reading lists
            'alternate_series': get_text('AlternateSeries'),
            'alternate_number': get_text('AlternateNumber'),
            'story_arc': get_text('StoryArc'),

            # Web link
            'web': get_text('Web'),

            # Store full XML for future use
            'raw_xml': xml_content.decode('utf-8')
        }
    except Exception as e:
        print(f"Error parsing ComicInfo.xml: {e}")
        return {}