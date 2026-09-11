local LrPrefs = import("LrPrefs")
local LrTasks = import("LrTasks")

local CatalogAssociationProbe = require("CatalogAssociationProbe")

local CatalogAssociationPublishServiceProvider = {}

local function incrementPreference(name, amount)
    local preferences = LrPrefs.prefsForPlugin()
    preferences[name] = (preferences[name] or 0) + amount
end

local function recordCallback(name, detail)
    local preferences = LrPrefs.prefsForPlugin()
    incrementPreference(name .. "Count", 1)
    preferences.lastCallback = name
    preferences.lastCallbackDetail = detail
end

local function writeProbeReport(phase)
    local preferences = LrPrefs.prefsForPlugin()
    local succeeded, message = LrTasks.pcall(CatalogAssociationProbe.writeReport, phase)
    preferences.reportWriteError = succeeded and nil or tostring(message)
end

CatalogAssociationPublishServiceProvider.supportsIncrementalPublish = "only"
CatalogAssociationPublishServiceProvider.exportPresetFields = {
    { key = "catalogAssociationOnly", default = true },
}
CatalogAssociationPublishServiceProvider.hideSections = {
    "exportLocation",
    "fileNaming",
    "fileSettings",
    "imageSettings",
    "outputSharpening",
    "metadata",
    "watermarking",
}
CatalogAssociationPublishServiceProvider.allowFileFormats = { "JPEG" }
CatalogAssociationPublishServiceProvider.canExportVideo = false
CatalogAssociationPublishServiceProvider.titleForPublishedCollection = "Catalog-only association"
CatalogAssociationPublishServiceProvider.titleForPublishedCollection_standalone = "Catalog-only association"
CatalogAssociationPublishServiceProvider.titleForGoToPublishedCollection = "disable"
CatalogAssociationPublishServiceProvider.titleForGoToPublishedPhoto = "disable"

function CatalogAssociationPublishServiceProvider.getCollectionBehaviorInfo(_)
    return {
        defaultCollectionName = "Catalog Association Only",
        defaultCollectionCanBeDeleted = false,
        canAddCollection = false,
        maxCollectionSetDepth = 0,
    }
end

function CatalogAssociationPublishServiceProvider.metadataThatTriggersRepublish(_)
    return { default = true }
end

function CatalogAssociationPublishServiceProvider.processRenderedPhotos(_, exportContext)
    local blocked = 0

    for _, rendition in exportContext.exportSession:renditions() do
        rendition:skipRender()
        rendition:uploadFailed(
            "Ticket #0067 blocks publishing and republication. This provider records catalog associations only."
        )
        blocked = blocked + 1
    end

    incrementPreference("blockedPublishRenditionCount", blocked)
    recordCallback("processRenderedPhotos", "blocked " .. tostring(blocked) .. " rendition(s) before rendering")
    writeProbeReport("publish_or_republish_blocked")
end

function CatalogAssociationPublishServiceProvider.shouldDeletePhotosFromServiceOnDeleteFromCatalog(
    _,
    nPhotos
)
    recordCallback("shouldDeletePhotosFromServiceOnDeleteFromCatalog", tostring(nPhotos) .. " catalog photo(s)")
    writeProbeReport("catalog_photo_delete_checked")
    return "ignore"
end

function CatalogAssociationPublishServiceProvider.deletePhotosFromPublishedCollection(
    _,
    arrayOfPhotoIds,
    deletedCallback,
    localCollectionId
)
    recordCallback(
        "deletePhotosFromPublishedCollection",
        tostring(#arrayOfPhotoIds) .. " local association(s) from collection " .. tostring(localCollectionId)
    )
    incrementPreference("localRemovalPhotoCount", #arrayOfPhotoIds)

    for _, photoId in ipairs(arrayOfPhotoIds) do
        deletedCallback(photoId)
    end
    writeProbeReport("local_association_removal_acknowledged")
end

function CatalogAssociationPublishServiceProvider.shouldDeletePublishedCollection(_, info)
    recordCallback("shouldDeletePublishedCollection", tostring(info.nPhotos or 0) .. " association(s)")
    writeProbeReport("published_collection_delete_checked")
    return "delete"
end

function CatalogAssociationPublishServiceProvider.deletePublishedCollection(_, info)
    recordCallback("deletePublishedCollection", tostring(info.remoteId or "no remote collection ID"))
    writeProbeReport("published_collection_deleted_locally")
end

function CatalogAssociationPublishServiceProvider.shouldDeletePublishService(_, info)
    recordCallback("shouldDeletePublishService", tostring(info.nPhotos or 0) .. " association(s)")
    writeProbeReport("publish_service_delete_checked")
    return "delete"
end

function CatalogAssociationPublishServiceProvider.willDeletePublishService(_, info)
    recordCallback("willDeletePublishService", tostring(info.nPhotos or 0) .. " association(s)")
    writeProbeReport("publish_service_deleted_locally")
end

return CatalogAssociationPublishServiceProvider
