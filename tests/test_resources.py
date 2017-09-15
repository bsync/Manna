import pytest
import os, shutil
import moto; moto.mock_s3().start() #Start before importing resources
from resources import Catalog

@pytest.fixture
def catalog():
    if os.path.exists("/tmp/massah"):
        shutil.rmtree("/tmp/massah")
    yield Catalog("/tmp/massah", bucket_name="massah")
    
def test_manna(catalog):

    assert catalog.listing() == [ ]
    catalog.addSeries("seriesA", description="A Test series")
    catalog.addSeries("seriesB", "Another Test series")

    assert catalog.listing() == [ "seriesA", "seriesB" ]

    seriesList = catalog.series()
    assert len(seriesList) == 2
    seriesA, seriesB = seriesList
    assert seriesA.name == 'seriesA'
    assert seriesB.name == 'seriesB'
    _test_series(*seriesList)

def _test_series(seriesA, seriesB):
    dirpath = os.path.dirname(__file__)
    assert seriesA.listing() + seriesB.listing() == []
    seriesA.addLesson(os.path.join(dirpath,"Lesson#001.mp4"))
    seriesA.addLesson(os.path.join(dirpath,"Lesson#002.mp4"))
    assert seriesA.listing() == [ "Lesson#001.mp4", "Lesson#002.mp4" ]
    assert len(seriesA) == 2

