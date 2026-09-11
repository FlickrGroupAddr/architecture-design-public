local LrApplication = import("LrApplication")
local LrDate = import("LrDate")
local LrDialogs = import("LrDialogs")
local LrDigest = import("LrDigest")
local LrFileUtils = import("LrFileUtils")
local LrPathUtils = import("LrPathUtils")
local LrPrefs = import("LrPrefs")
local LrTasks = import("LrTasks")

local Json = require("dkjson")

local CatalogAssociationProbe = {}

local ADOBE_FLICKR_PLUGIN_ID = "com.adobe.lightroom.export.flickr"
local ASSOCIATION_COLLECTION_NAME = "Catalog Association Only"
local EXPECTED_FIXTURE_SHA2_256 = "a64d5bfa01b27dcb6772b388baaef4e9e6289886bd40f2a8e26c573f65014968"
local FIXTURE_FILENAME = "catalog-association-0067.png"
local REPORT_DIRECTORY = "C:\\Temp"
local REPORT_PATH = "C:\\Temp\\FGA-catalog-association-0067.json"

local function fixturePath()
    return LrPathUtils.child(LrPathUtils.child(_PLUGIN.path, "catalog-association-fixtures"), FIXTURE_FILENAME)
end

local function resetAudit()
    local preferences = LrPrefs.prefsForPlugin()
    preferences.blockedPublishRenditionCount = 0
    preferences.processRenderedPhotosCount = 0
    preferences.shouldDeletePhotosFromServiceOnDeleteFromCatalogCount = 0
    preferences.deletePhotosFromPublishedCollectionCount = 0
    preferences.localRemovalPhotoCount = 0
    preferences.shouldDeletePublishedCollectionCount = 0
    preferences.deletePublishedCollectionCount = 0
    preferences.shouldDeletePublishServiceCount = 0
    preferences.willDeletePublishServiceCount = 0
    preferences.lastCallback = "none"
    preferences.lastCallbackDetail = "none"
    preferences.reportWriteError = nil
    preferences.sourceSnapshot = nil
end

local function confirmDisposableCatalog(catalog, action)
    local result = LrDialogs.confirm(
        "Ticket #0067 — disposable catalog only",
        string.format(
            "%s\n\nCatalog: %s\nFixture: %s\n\n"
                .. "Continue only if this is the purpose-built disposable catalog. The command never calls Flickr.",
            action,
            catalog:getPath(),
            fixturePath()
        ),
        "Continue",
        "Cancel"
    )
    return result == "ok"
end

local function fileSha2_256(path)
    local file, openMessage = io.open(path, "rb")
    if not file then
        error("Could not read a ticket #0067 fixture candidate: " .. tostring(openMessage))
    end
    local payload = file:read("*a")
    local closed, closeMessage = file:close()
    if not payload then
        error("Could not read the complete ticket #0067 fixture candidate")
    end
    if not closed then
        error("Could not close a ticket #0067 fixture candidate: " .. tostring(closeMessage))
    end
    local digestHex = LrDigest.SHA256.digest(payload)
    return string.lower(digestHex)
end

local function photoFixtureDigest(photo)
    return fileSha2_256(photo:getRawMetadata("path"))
end

local function photoIsFixture(photo)
    return photoFixtureDigest(photo) == EXPECTED_FIXTURE_SHA2_256
end

local function fixtureRecordsForPlugin(catalog, pluginId)
    local records = {}
    for _, service in ipairs(catalog:getPublishServices(pluginId)) do
        for _, collection in ipairs(service:getChildCollections()) do
            for _, publishedPhoto in ipairs(collection:getPublishedPhotos()) do
                if photoIsFixture(publishedPhoto:getPhoto()) then
                    records[#records + 1] = {
                        service = service,
                        collection = collection,
                        publishedPhoto = publishedPhoto,
                    }
                end
            end
        end
    end
    return records
end

local function sourceRecords(catalog)
    return fixtureRecordsForPlugin(catalog, ADOBE_FLICKR_PLUGIN_ID)
end

local function associationRecords(catalog)
    return fixtureRecordsForPlugin(catalog, _PLUGIN.id)
end

local function publishServiceInventory(catalog)
    local inventory = {}
    for _, service in ipairs(catalog:getPublishServices(nil)) do
        local fixturePublishedRecordCount = 0
        for _, collection in ipairs(service:getChildCollections()) do
            for _, publishedPhoto in ipairs(collection:getPublishedPhotos()) do
                if photoIsFixture(publishedPhoto:getPhoto()) then
                    fixturePublishedRecordCount = fixturePublishedRecordCount + 1
                end
            end
        end
        inventory[#inventory + 1] = {
            pluginId = service:getPluginId(),
            serviceName = service:getName(),
            serviceLocalIdentifier = service.localIdentifier,
            childCollectionCount = #service:getChildCollections(),
            fixturePublishedRecordCount = fixturePublishedRecordCount,
        }
    end
    return inventory
end

local function requireOneRecord(records, description)
    if #records ~= 1 then
        error(string.format("Expected exactly one %s; found %d", description, #records))
    end
    return records[1]
end

local function requireAssociationCollection(catalog)
    local services = catalog:getPublishServices(_PLUGIN.id)
    if #services ~= 1 then
        error(
            "Create exactly one ‘FGA Catalog Association Probe’ service in Publishing Manager before continuing"
        )
    end

    local matching = {}
    for _, collection in ipairs(services[1]:getChildCollections()) do
        if collection:getName() == ASSOCIATION_COLLECTION_NAME then
            matching[#matching + 1] = collection
        end
    end
    return requireOneRecord(matching, "FGA catalog-association collection")
end

local function recordSnapshot(record)
    local publishedPhoto = record.publishedPhoto
    return table.concat({
        tostring(record.service.localIdentifier),
        tostring(record.collection.localIdentifier),
        tostring(publishedPhoto:getRemoteId()),
        tostring(publishedPhoto:getRemoteUrl()),
        tostring(publishedPhoto:getEditedFlag()),
        tostring(publishedPhoto:getPublishCount()),
    }, "|")
end

local function describeRecord(label, record)
    if not record then
        return label .. ": absent"
    end
    local publishedPhoto = record.publishedPhoto
    return string.format(
        "%s:\n  service: %s (%s)\n  collection: %s (%s)\n  remote ID: %s\n  remote URL: %s\n"
            .. "  edited: %s\n  publish count: %s",
        label,
        record.service:getName(),
        tostring(record.service.localIdentifier),
        record.collection:getName(),
        tostring(record.collection.localIdentifier),
        tostring(publishedPhoto:getRemoteId()),
        tostring(publishedPhoto:getRemoteUrl()),
        tostring(publishedPhoto:getEditedFlag()),
        tostring(publishedPhoto:getPublishCount())
    )
end

local function describeAudit()
    local preferences = LrPrefs.prefsForPlugin()
    return string.format(
        "Callback audit:\n  blocked publish renditions: %s\n  processRenderedPhotos calls: %s\n"
            .. "  local-removal callbacks: %s\n  locally removed associations: %s\n  catalog-delete checks: %s\n"
            .. "  last callback: %s — %s",
        tostring(preferences.blockedPublishRenditionCount or 0),
        tostring(preferences.processRenderedPhotosCount or 0),
        tostring(preferences.deletePhotosFromPublishedCollectionCount or 0),
        tostring(preferences.localRemovalPhotoCount or 0),
        tostring(preferences.shouldDeletePhotosFromServiceOnDeleteFromCatalogCount or 0),
        tostring(preferences.lastCallback or "none"),
        tostring(preferences.lastCallbackDetail or "none")
    )
end

local function recordData(record)
    local publishedPhoto = record.publishedPhoto
    local photo = publishedPhoto:getPhoto()
    return {
        serviceName = record.service:getName(),
        serviceLocalIdentifier = record.service.localIdentifier,
        collectionName = record.collection:getName(),
        collectionLocalIdentifier = record.collection.localIdentifier,
        remoteId = publishedPhoto:getRemoteId(),
        remoteUrl = publishedPhoto:getRemoteUrl(),
        edited = publishedPhoto:getEditedFlag(),
        publishCount = publishedPhoto:getPublishCount(),
        catalogPhotoPath = photo:getRawMetadata("path"),
        fixtureSha2_256 = photoFixtureDigest(photo),
    }
end

local function recordsData(records)
    local result = {}
    for _, record in ipairs(records) do
        result[#result + 1] = recordData(record)
    end
    return result
end

local function auditData()
    local preferences = LrPrefs.prefsForPlugin()
    return {
        blockedPublishRenditionCount = preferences.blockedPublishRenditionCount or 0,
        processRenderedPhotosCount = preferences.processRenderedPhotosCount or 0,
        shouldDeletePhotosFromServiceOnDeleteFromCatalogCount =
            preferences.shouldDeletePhotosFromServiceOnDeleteFromCatalogCount or 0,
        deletePhotosFromPublishedCollectionCount = preferences.deletePhotosFromPublishedCollectionCount or 0,
        localRemovalPhotoCount = preferences.localRemovalPhotoCount or 0,
        shouldDeletePublishedCollectionCount = preferences.shouldDeletePublishedCollectionCount or 0,
        deletePublishedCollectionCount = preferences.deletePublishedCollectionCount or 0,
        shouldDeletePublishServiceCount = preferences.shouldDeletePublishServiceCount or 0,
        willDeletePublishServiceCount = preferences.willDeletePublishServiceCount or 0,
        lastCallback = preferences.lastCallback or "none",
        lastCallbackDetail = preferences.lastCallbackDetail or "none",
        reportWriteError = preferences.reportWriteError,
    }
end

local function replaceReport(report)
    local created, createMessage = LrFileUtils.createAllDirectories(REPORT_DIRECTORY)
    if not created then
        error("Could not create the probe report directory: " .. tostring(createMessage))
    end

    local temporaryPath = REPORT_PATH .. ".tmp"
    local file, openMessage = io.open(temporaryPath, "wb")
    if not file then
        error("Could not create the probe report: " .. tostring(openMessage))
    end

    local encoded = Json.encode(report, { indent = true }) .. "\n"
    local written, writeMessage = file:write(encoded)
    local closed, closeMessage = file:close()
    if not written then
        error("Could not write the probe report: " .. tostring(writeMessage))
    end
    if not closed then
        error("Could not close the probe report: " .. tostring(closeMessage))
    end

    if LrFileUtils.exists(REPORT_PATH) then
        local deleted, deleteMessage = LrFileUtils.delete(REPORT_PATH)
        if not deleted then
            error("Could not replace the previous probe report: " .. tostring(deleteMessage))
        end
    end

    local moved, moveMessage = LrFileUtils.move(temporaryPath, REPORT_PATH)
    if not moved then
        error("Could not publish the complete probe report: " .. tostring(moveMessage))
    end
end


function CatalogAssociationProbe.writeReport(phase, failure)
    local catalog = LrApplication.activeCatalog()
    local canonicalPhoto = catalog:findPhotoByPath(fixturePath())
    local sources = sourceRecords(catalog)
    local associations = associationRecords(catalog)
    local preferences = LrPrefs.prefsForPlugin()
    local sourceSnapshotState = "not_recorded"
    if preferences.sourceSnapshot and #sources == 1 then
        sourceSnapshotState = preferences.sourceSnapshot == recordSnapshot(sources[1]) and "matches" or "differs"
    end

    replaceReport({
        schema = 1,
        ticket = 67,
        probe = "catalog-only-existing-photo-association",
        phase = phase,
        writtenAt = LrDate.timeToW3CDate(LrDate.currentTime()),
        outputPath = REPORT_PATH,
        catalogPath = catalog:getPath(),
        fixturePath = fixturePath(),
        fixtureImported = canonicalPhoto ~= nil or #sources > 0,
        canonicalFixtureImported = canonicalPhoto ~= nil,
        expectedFixtureSha2_256 = EXPECTED_FIXTURE_SHA2_256,
        sourceRecordCount = #sources,
        sourceRecords = recordsData(sources),
        associationRecordCount = #associations,
        associationRecords = recordsData(associations),
        savedSourceSnapshot = sourceSnapshotState,
        publishServices = publishServiceInventory(catalog),
        callbackAudit = auditData(),
        failure = failure,
    })
end


local function reportThenShow(phase, title, message)
    CatalogAssociationProbe.writeReport(phase)
    LrDialogs.message(title, message, "info")
    return phase, true
end


function CatalogAssociationProbe.run(phase, action)
    local succeeded, result, reportWritten = LrTasks.pcall(action)
    if not succeeded then
        local reportSucceeded, reportMessage = LrTasks.pcall(
            CatalogAssociationProbe.writeReport,
            phase .. "_failed",
            result
        )
        if not reportSucceeded then
            error(tostring(result) .. "\nProbe report also failed: " .. tostring(reportMessage))
        end
        error(result)
    end

    if not reportWritten then
        CatalogAssociationProbe.writeReport(result or phase .. "_completed")
    end
end

function CatalogAssociationProbe.prepare()
    local catalog = LrApplication.activeCatalog()
    if not confirmDisposableCatalog(catalog, "Import and select the deterministic public-safe fixture.") then
        return "prepare_canceled"
    end

    local sources = sourceRecords(catalog)
    if #sources > 1 then
        error(string.format("Expected at most one Adobe Flickr fixture source record; found %d", #sources))
    end

    local photo = sources[1] and sources[1].publishedPhoto:getPhoto() or catalog:findPhotoByPath(fixturePath())
    if not photo then
        catalog:withWriteAccessDo("Import ticket #0067 fixture", function()
            photo = catalog:addPhoto(fixturePath())
        end)
    end
    catalog:setSelectedPhotos(photo, {})
    resetAudit()

    return reportThenShow(
        "fixture_prepared",
        "Ticket #0067 fixture prepared",
        "The exact fixture is imported and selected.\n\n"
            .. "Next, publish it exactly once through Adobe’s Flickr publish service as Safe, public, photo, "
            .. "with no album or group membership. Then create one ‘FGA Catalog Association Probe’ service "
            .. "in Publishing Manager."
    )
end


function CatalogAssociationProbe.createAssociation()
    local catalog = LrApplication.activeCatalog()
    if
        not confirmDisposableCatalog(
            catalog,
            "Create one provider-scoped catalog association for the selected fixture."
        )
    then
        return "create_association_canceled"
    end

    local source = requireOneRecord(sourceRecords(catalog), "verified Adobe Flickr published-photo source record")
    local photo = source.publishedPhoto:getPhoto()
    local sourceRemoteId = source.publishedPhoto:getRemoteId()
    local sourceRemoteUrl = source.publishedPhoto:getRemoteUrl()
    if not sourceRemoteId or tostring(sourceRemoteId) == "" then
        error("The Adobe Flickr source record has no remote photo ID")
    end

    local associationCollection = requireAssociationCollection(catalog)
    local before = recordSnapshot(source)
    catalog:withWriteAccessDo("Create ticket #0067 catalog-only association", function()
        associationCollection:addPhotoByRemoteId(photo, sourceRemoteId, sourceRemoteUrl, true)
    end)

    local sourceAfter = requireOneRecord(sourceRecords(catalog), "verified Adobe Flickr published-photo source record")
    local after = recordSnapshot(sourceAfter)
    if before ~= after then
        error("The Adobe Flickr source publication record changed while the FGA catalog association was created")
    end

    local association = requireOneRecord(associationRecords(catalog), "FGA catalog-only association")
    local preferences = LrPrefs.prefsForPlugin()
    preferences.sourceSnapshot = before

    return reportThenShow(
        "association_created",
        "Catalog-only association created",
        describeRecord("Adobe Flickr source record", sourceAfter)
            .. "\n\n"
            .. describeRecord("FGA catalog-only association", association)
            .. "\n\nThe source snapshot was unchanged across addPhotoByRemoteId."
    )
end


function CatalogAssociationProbe.inspect()
    local catalog = LrApplication.activeCatalog()
    local sources = sourceRecords(catalog)
    local associations = associationRecords(catalog)
    local source = sources[1]
    local association = associations[1]
    local preferences = LrPrefs.prefsForPlugin()
    local sourceMatches = source and preferences.sourceSnapshot == recordSnapshot(source)

    return reportThenShow(
        "association_inspected",
        "Ticket #0067 catalog state",
        string.format(
            "Catalog: %s\nSource record count: %d\nFGA association count: %d\nSaved source snapshot matches: %s\n\n",
            catalog:getPath(),
            #sources,
            #associations,
            tostring(sourceMatches)
        )
            .. describeRecord("Adobe Flickr source record", source)
            .. "\n\n"
            .. describeRecord("FGA catalog-only association", association)
            .. "\n\n"
            .. describeAudit()
    )
end


function CatalogAssociationProbe.removeAssociation()
    local catalog = LrApplication.activeCatalog()
    local association = requireOneRecord(associationRecords(catalog), "FGA catalog-only association")
    local photo = association.publishedPhoto:getPhoto()
    if not confirmDisposableCatalog(catalog, "Remove only the selected fixture’s FGA catalog association.") then
        return "remove_association_canceled"
    end

    catalog:withWriteAccessDo("Remove ticket #0067 catalog-only association", function()
        association.collection:removePhotos({ photo })
    end)
    return reportThenShow(
        "association_removed_locally",
        "Catalog association removed locally",
        "The Adobe Flickr source record and Flickr photo were not touched. In the FGA association collection, "
            .. "click Publish to exercise the local-removal callback, then run the inspection command."
    )
end


return CatalogAssociationProbe
