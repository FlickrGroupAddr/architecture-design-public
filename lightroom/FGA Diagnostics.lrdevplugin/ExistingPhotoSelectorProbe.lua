local LrBinding = import("LrBinding")
local LrDate = import("LrDate")
local LrDialogs = import("LrDialogs")
local LrFileUtils = import("LrFileUtils")
local LrPathUtils = import("LrPathUtils")
local LrView = import("LrView")

local ExistingPhotoSelectorProbe = {}

local FIXTURE_PAGES = {
    {
        observedAt = "2026-08-26T14:00:00.123456Z",
        total = 6,
        photos = {
            {
                flickrPhotoId = "fixture-photo-id-000001",
                title = "Blue horizon and pale window",
                dateUploaded = "2026-08-19 09:42 UTC",
                dateTaken = "2026-08-18 18:12",
                fixture = "thumbnail-01.png",
            },
            {
                flickrPhotoId = "fixture-photo-id-000002",
                title = "Warm diagonal study",
                dateUploaded = "2026-08-18 21:17 UTC",
                dateTaken = "2026-08-16 11:05",
                fixture = "thumbnail-02.png",
            },
            {
                flickrPhotoId = "fixture-photo-id-000003",
                title = "Green field grid",
                dateUploaded = "2026-08-17 13:08 UTC",
                dateTaken = "2026-08-15 16:31",
                fixture = "thumbnail-03.png",
            },
        },
    },
    {
        observedAt = "2026-08-26T14:00:01.123456Z",
        total = 6,
        photos = {
            {
                flickrPhotoId = "fixture-photo-id-000004",
                title = "Violet circle and stripes",
                dateUploaded = "2026-08-16 22:44 UTC",
                dateTaken = "2026-08-14 08:29",
                fixture = "thumbnail-04.png",
            },
            {
                flickrPhotoId = "fixture-photo-id-000005",
                title = "Blue crossing",
                dateUploaded = "2026-08-15 17:36 UTC",
                dateTaken = "2026-08-13 19:54",
                fixture = "thumbnail-05.png",
            },
            {
                flickrPhotoId = "fixture-photo-id-000006",
                title = "Gray bars with gold band",
                dateUploaded = "2026-08-14 12:03 UTC",
                dateTaken = "2026-08-12 07:47",
                fixture = "thumbnail-06.png",
            },
        },
    },
}

local function fixtureRoot()
    return LrPathUtils.child(_PLUGIN.path, "selector-fixtures")
end


local function createCacheDirectory()
    local temporaryRoot = LrPathUtils.getStandardFilePath("temp")
    local probeRoot = LrPathUtils.child(temporaryRoot, "fga-existing-photo-selector-probe")
    local timestamp = LrDate.timeToUserFormat(LrDate.currentTime(), "%Y%m%d-%H%M%S", false)
    local runDirectory = LrPathUtils.child(probeRoot, timestamp)
    local created, createMessage = LrFileUtils.createAllDirectories(runDirectory)

    if not created then
        error("Could not create selector thumbnail cache: " .. tostring(createMessage))
    end

    return runDirectory
end


local function removeCache(path)
    if path and LrFileUtils.exists(path) then
        local deleted, deleteMessage = LrFileUtils.delete(path)

        if not deleted then
            error("Could not remove selector thumbnail cache: " .. tostring(deleteMessage))
        end
    end
end


local function stageFixturePage(runDirectory, pageNumber)
    local fixturePage = FIXTURE_PAGES[pageNumber]

    if not fixturePage then
        error("Fixture page is outside the available range")
    end

    local pageDirectory = LrPathUtils.child(runDirectory, "page-" .. tostring(pageNumber))
    local created, createMessage = LrFileUtils.createAllDirectories(pageDirectory)

    if not created then
        error("Could not create page thumbnail cache: " .. tostring(createMessage))
    end

    local photos = {}

    for index, fixture in ipairs(fixturePage.photos) do
        local source = LrPathUtils.child(fixtureRoot(), fixture.fixture)
        local destination = LrPathUtils.child(pageDirectory, string.format("thumb-%02d.png", index))
        local copied, copyMessage = LrFileUtils.copy(source, destination)

        if not copied then
            error("Could not stage required selector thumbnail: " .. tostring(copyMessage))
        end

        photos[#photos + 1] = {
            flickrPhotoId = fixture.flickrPhotoId,
            title = fixture.title,
            dateUploaded = fixture.dateUploaded,
            dateTaken = fixture.dateTaken,
            thumbnailPath = destination,
        }
    end

    return {
        page = pageNumber,
        pages = #FIXTURE_PAGES,
        total = fixturePage.total,
        observedAt = fixturePage.observedAt,
        photos = photos,
        cacheDirectory = pageDirectory,
    }
end


local function makePhotoRow(factory, photo)
    return factory:row {
        spacing = factory:control_spacing(),
        fill_horizontal = 1,

        factory:radio_button {
            title = "",
            value = LrView.bind("selectedPhotoId"),
            checked_value = photo.flickrPhotoId,
        },

        factory:picture {
            value = photo.thumbnailPath,
            width = 160,
            height = 120,
            frame_width = 1,
        },

        factory:column {
            spacing = factory:label_spacing(),
            width = 430,

            factory:static_text {
                title = photo.title,
                width_in_chars = 54,
                height_in_lines = 2,
            },
            factory:static_text {
                title = "Taken: " .. photo.dateTaken,
                width_in_chars = 54,
            },
            factory:static_text {
                title = "Uploaded: " .. photo.dateUploaded,
                width_in_chars = 54,
            },
            factory:static_text {
                title = "Exact Flickr photo ID: " .. photo.flickrPhotoId,
                width_in_chars = 54,
                selectable = true,
            },
        },
    }
end


local function showPage(context, page)
    local factory = LrView.osFactory()
    local properties = LrBinding.makePropertyTable(context)
    properties.selectedPhotoId = nil

    local photoColumnArguments = {
        bind_to_object = properties,
        spacing = factory:control_spacing(),
        fill_horizontal = 1,
    }

    for _, photo in ipairs(page.photos) do
        photoColumnArguments[#photoColumnArguments + 1] = makePhotoRow(factory, photo)
    end

    local contents = factory:column {
        bind_to_object = properties,
        spacing = factory:control_spacing(),
        fill_horizontal = 1,

        factory:static_text {
            title = "Development fixture only — no Flickr, catalog, upload, replacement, or group mutation occurs.",
            width_in_chars = 78,
            height_in_lines = 2,
        },
        factory:static_text {
            title = string.format(
                "Public-photo observation %s — page %d of %d — %d total",
                page.observedAt,
                page.page,
                page.pages,
                page.total
            ),
            width_in_chars = 78,
        },
        factory:scrolled_view {
            width = 700,
            height = 430,
            horizontal_scroller = false,
            vertical_scroller = true,
            factory:column(photoColumnArguments),
        },
    }

    local result = LrDialogs.presentModalDialog {
        title = "Add Groups to Existing Flickr Photo… — Selector Probe",
        contents = contents,
        actionVerb = "Choose Photo",
        actionBinding = {
            enabled = {
                bind_to_object = properties,
                key = "selectedPhotoId",
                transform = function(value)
                    return value ~= nil
                end,
            },
        },
        cancelVerb = "Cancel",
        accessoryView = factory:row {
            spacing = factory:control_spacing(),
            factory:push_button {
                title = "Previous",
                enabled = page.page > 1,
                action = function(button)
                    LrDialogs.stopModalWithResult(button, "previous")
                end,
            },
            factory:push_button {
                title = "Next",
                enabled = page.page < page.pages,
                action = function(button)
                    LrDialogs.stopModalWithResult(button, "next")
                end,
            },
        },
        resizable = "vertically",
        save_frame = "fgaExistingPhotoSelectorProbe",
    }

    return result, properties.selectedPhotoId
end


local function selectPhoto(context, loadPage)
    local pageNumber = 1

    while true do
        local loaded, pageOrMessage = pcall(loadPage, pageNumber)

        if not loaded then
            LrDialogs.message(
                "Public photos unavailable",
                "The complete page and all required thumbnails could not be loaded.\n\n"
                    .. tostring(pageOrMessage),
                "critical"
            )
            return nil
        end

        local page = pageOrMessage
        local result, selectedPhotoId = showPage(context, page)
        removeCache(page.cacheDirectory)

        if result == "ok" then
            return selectedPhotoId
        elseif result == "next" then
            pageNumber = pageNumber + 1
        elseif result == "previous" then
            pageNumber = pageNumber - 1
        else
            return nil
        end
    end
end


function ExistingPhotoSelectorProbe.run(context)
    local runDirectory = createCacheDirectory()
    context:addCleanupHandler(function()
        removeCache(runDirectory)
    end)

    local selectedPhotoId = selectPhoto(context, function(pageNumber)
        return stageFixturePage(runDirectory, pageNumber)
    end)

    if selectedPhotoId then
        LrDialogs.message(
            "Selector probe result",
            "Selected exact fixture ID:\n" .. selectedPhotoId .. "\n\nNo external or catalog state changed.",
            "info"
        )
    end
end


return ExistingPhotoSelectorProbe
