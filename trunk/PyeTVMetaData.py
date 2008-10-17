#
# classes to deal with recording metadata previews (screenshots, description text, etc)
#

import objc
import string
from PyFR.BackRow import *
from Logger import log
from etv import ETV


class PyeTVMediaAsset(BRSimpleMediaAsset):
    """
    Defines a FrontRow media asset from a EyeTV recording  
    """

    def initWithRecording_(self, rec):
        log("PyeTVMediaAsset inited for rec %s" % rec.GetTitle());
        BRSimpleMediaAsset.initWithMediaURL_(self,"")
        self.rec=rec
        self.firstTime=True
        self.IsSeries=False
        return self

    def initWithSeriesEpisode_(self, rec):
        log("PyeTVMediaAsset inited for rec %s" % rec.GetTitle());
        BRSimpleMediaAsset.initWithMediaURL_(self,"")
        self.rec=rec
        self.firstTime=True
        self.IsSeries=True
        return self

    def coverArt(self):
        log("PyeTVMediaAsset::coverArt")
        return BRImage.imageWithPath_(self.rec.GetPreviewImagePath())

    # the first time this is called, it's apparently being asked if it conforms to a BRMediaAsset protocol.  The next time, a collection.
    def conformsToProtocol_(self, protocol):
         log("PyeTVMediaAsset::conformsToProtocol: %s" % repr(protocol))
         if self.firstTime:
             self.firstTime=False
             return True
         return False

class PyeTVMetadataPopulator(NSObject):
    """
    The populator class to be returned by PyeTVMetadataPopulatorFactor
    """
    def init(self):
        NSObject.init(self);
        return self

    def populateLayer_fromAsset_(self, layer, asset):
        log("We want to do magic stuff here for layer %s and asset %s" % (repr(layer), repr(asset)))
        if asset.IsSeries:
            return
        layer.setTitle_(asset.rec.GetTitle())
        layer.setSummary_(asset.rec.GetDescription())
        labels=[
            "Episode",
            "Channel",
            "Position",
            "Recorded at"
            ]
        data=[
            asset.rec.GetEpisode(),
            asset.rec.GetChannelStr(),
            asset.rec.GetPlaybackPosition(True) + " of " +asset.rec.GetDuration(True),
            asset.rec.GetStartTime()
            ]
        layer.setMetadata_withLabels_(data,labels)
        return

    def axMetadataFromAsset_(self, asset):
        log("called axMetadataFromAsset %s" % repr(asset))
        return None

class PyeTVMetadataPopulatorFactory(BRSingleton):
    """
    Custom metadata populator factory which will return a populator which understands EyeTV recordings
    """

    __Instance = None

    def init(self):
        __Instance=self
        self.pop=PyeTVMetadataPopulator.alloc().init()
        return BRSingleton.init(self)

    # Note: this isn't really a good singleton implementation, but it's good enough for our purposes here
    @classmethod
    def singleton(self):
        return self.__Instance

    def populatorForAsset_(self, asset):
        return self.pop


class PyeTVPreviewMetadataController(BRMetadataPreviewController):
    """
    A Front Row controller which shows a preview based on metadata from a EyeTV recording
    """

    def initWithRecording_(self, rec):
        BRMetadataPreviewController.init(self)
        asset=PyeTVMediaAsset.alloc().initWithRecording_(rec)
        self.setAsset_(asset)
        self.setShowsMetadataImmediately_(True) # could comment this out for a bigger look at the screenshot, but the md is more important
        return self

    def initWithSeriesEpisode_(self, rec):
        BRMetadataPreviewController.init(self)
        asset=PyeTVMediaAsset.alloc().initWithSeriesEpisode_(rec)
        self.setAsset_(asset)
        #self.setShowsMetadataImmediately_(True) 
        return self

    def _updateMetadataLayer(self):
        # create temporary populator factory and replace standard one ---
        # I don't know how to get the standard populator to properly identify the asset,
        # and even if I did, one of the pre-defined assets probably wouldn't populate with the fields I want!

        # and yes, this is a horrible abuse of setSingleton_.
        log("PyeTVPreviewMetadataLayerController::_updateMetadataLayer")
        oldPopFactory=BRMetadataPopulatorFactory.sharedInstance()
        BRMetadataPopulatorFactory.setSingleton_(PyeTVMetadataPopulatorFactory.alloc().init())
        BRMetadataPreviewController._updateMetadataLayer(self)
        BRMetadataPopulatorFactory.setSingleton_(oldPopFactory)
