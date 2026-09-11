local LrApplication = import("LrApplication")
local LrDate = import("LrDate")
local LrDialogs = import("LrDialogs")
local LrExportSession = import("LrExportSession")
local LrFileUtils = import("LrFileUtils")
local LrHttp = import("LrHttp")
local LrPathUtils = import("LrPathUtils")
local LrProgressScope = import("LrProgressScope")
local LrXml = import("LrXml")

local Json = require("dkjson")

local DirectUploadProbe = {}

local SIGNER_URL = "http://127.0.0.1:8765/api/v001/upload-authorizations"
local FLICKR_UPLOAD_URL = "https://up.flickr.com/services/upload/"
local function localSelection()
    local path = LrPathUtils.child(_PLUGIN.path, "DirectUpload.local.json")
    if LrFileUtils.exists(path) ~= "file" then
        error("Configure the ignored DirectUpload.local.json before running this probe")
    end
    local content = LrFileUtils.readFile(path)
    if type(content) ~= "string" or #content > 4096 then
        error("The local probe configuration is unavailable or oversized")
    end
    local config, _, decodeError = Json.decode(content)
    if decodeError or type(config) ~= "table" then
        error("The local probe configuration must be a JSON object")
    end
    if type(config.photoUuid) ~= "string" or #config.photoUuid ~= 36
        or not string.match(config.photoUuid, "^[%x%-]+$")
        or config.photoUuid == "00000000-0000-4000-8000-000000000000"
        or type(config.sourceFilename) ~= "string" or config.sourceFilename == ""
        or string.find(config.sourceFilename, "[/\\]")
        or type(config.publicFlickrUrl) ~= "string"
        or not string.match(config.publicFlickrUrl, "^https://www%.flickr%.com/photos/[%w_%-]+/%d+/$")
    then
        error("Configure one verified public photo using the documented local fields")
    end
    return config
end


local function renderSettings(outputDirectory)
    return {
        LR_collisionHandling = "overwrite",
        LR_export_bitDepth = 8,
        LR_export_colorSpace = "sRGB",
        LR_export_destinationPathPrefix = outputDirectory,
        LR_export_destinationType = "specificFolder",
        LR_export_postProcessing = "doNothing",
        LR_export_useParentFolder = false,
        LR_export_useSubfolder = false,
        LR_extensionCase = "lowercase",
        LR_format = "PNG",
        LR_outputSharpeningOn = false,
        LR_png_interlaced = false,
        LR_renamingTokensOn = false,
        LR_size_doConstrain = false,
        LR_useWatermark = false,
    }
end

local function createRunDirectory(photoUuid)
    local temporaryRoot = LrPathUtils.getStandardFilePath("temp")
    local probeRoot = LrPathUtils.child(temporaryRoot, "fga-lightroom-upload-probe")
    local runName = LrDate.timeToUserFormat(LrDate.currentTime(), "%Y%m%d-%H%M%S", false) .. "-" .. photoUuid
    local runDirectory = LrPathUtils.child(probeRoot, runName)
    local created, createMessage = LrFileUtils.createAllDirectories(runDirectory)

    if not created then
        error("Could not create temporary render directory: " .. tostring(createMessage))
    end

    return runDirectory
end

local function renderPhoto(context, photo, runDirectory)
    local progress = LrProgressScope({
        title = "FGA Lightroom multipart probe",
        functionContext = context,
    })
    progress:setCancelable(false)
    progress:setCaption("Rendering verified public photo as 8-bit sRGB PNG")

    local session = LrExportSession({
        photosToExport = { photo },
        exportSettings = renderSettings(runDirectory),
    })
    local renderedPath = nil

    for _, rendition in session:renditions({
        progressScope = progress,
        stopIfCanceled = false,
    }) do
        local success, pathOrMessage = rendition:waitForRender()

        if not success then
            progress:done()
            error("Lightroom PNG render failed: " .. tostring(pathOrMessage))
        end

        renderedPath = pathOrMessage
    end

    progress:done()

    if not renderedPath or LrFileUtils.exists(renderedPath) ~= "file" then
        error("Lightroom did not produce the expected PNG render")
    end

    return renderedPath
end

local function requireHttpSuccess(body, headers, operation)
    local status = headers and headers.status or nil

    if not body then
        error(operation .. " did not return a response body")
    end

    if status ~= 200 then
        error(string.format("%s returned HTTP %s", operation, tostring(status)))
    end

    return body
end

local function requestSigningEnvelope()
    local responseBody, responseHeaders = LrHttp.post(
        SIGNER_URL,
        "{}",
        {
            { field = "Content-Type", value = "application/json" },
        },
        "POST",
        15
    )
    requireHttpSuccess(responseBody, responseHeaders, "Local FGA signer")

    local envelope, _, decodeError = Json.decode(responseBody)

    if decodeError then
        error("Local FGA signer returned invalid JSON: " .. tostring(decodeError))
    end

    if type(envelope) ~= "table" or envelope.schemaVersion ~= 1 then
        error("Local FGA signer returned an unsupported envelope")
    end

    if envelope.uploadUrl ~= FLICKR_UPLOAD_URL then
        error("Local FGA signer returned an unexpected upload URL")
    end

    if type(envelope.authorizationHeader) ~= "string" or envelope.authorizationHeader == "" then
        error("Local FGA signer omitted the authorization header")
    end

    if type(envelope.metadata) ~= "table" or envelope.metadata.photo ~= nil then
        error("Local FGA signer returned invalid upload metadata")
    end

    return envelope
end

local function sortedMetadataNames(metadata)
    local names = {}

    for name, value in pairs(metadata) do
        if type(name) ~= "string" or type(value) ~= "string" then
            error("Local FGA signer returned non-string upload metadata")
        end

        names[#names + 1] = name
    end

    table.sort(names)
    return names
end

local function findElement(node, elementName)
    if not node then
        return nil
    end

    if node:type() == "element" and node:name() == elementName then
        return node
    end

    local childCount = node:childCount() or 0

    for index = 1, childCount do
        local found = findElement(node:childAtIndex(index), elementName)

        if found then
            return found
        end
    end

    return nil
end

local function parseFlickrPhotoId(responseBody)
    local document = LrXml.parseXml(responseBody)
    local photoIdElement = findElement(document, "photoid")
    local flickrPhotoId = photoIdElement and photoIdElement:text() or nil

    if flickrPhotoId and flickrPhotoId ~= "" then
        return flickrPhotoId
    end

    local errorElement = findElement(document, "err")

    if errorElement then
        local attributes = errorElement:attributes() or {}
        local code = attributes.code and attributes.code.value or "unknown"
        local message = attributes.msg and attributes.msg.value or "unknown Flickr error"
        error(string.format("Flickr rejected the upload (code %s): %s", tostring(code), tostring(message)))
    end

    error("Flickr upload response did not contain a Flickr photo ID")
end

local function uploadPng(context, imagePath, envelope)
    local chunks = {}

    for _, name in ipairs(sortedMetadataNames(envelope.metadata)) do
        chunks[#chunks + 1] = { name = name, value = envelope.metadata[name] }
    end

    chunks[#chunks + 1] = {
        name = "photo",
        fileName = LrPathUtils.leafName(imagePath),
        filePath = imagePath,
        contentType = "image/png",
    }

    local progress = LrProgressScope({
        title = "FGA direct Flickr upload probe",
        functionContext = context,
    })
    progress:setCancelable(false)
    progress:setCaption("Streaming PNG directly from Lightroom to Flickr")

    local responseBody, responseHeaders = LrHttp.postMultipart(
        envelope.uploadUrl,
        chunks,
        {
            { field = "Authorization", value = envelope.authorizationHeader },
        },
        300,
        function(portionComplete)
            progress:setPortionComplete(portionComplete, 1)
        end
    )
    progress:done()
    requireHttpSuccess(responseBody, responseHeaders, "Flickr upload")
    return parseFlickrPhotoId(responseBody)
end

function DirectUploadProbe.run(context)
    local selection = localSelection()
    local catalog = LrApplication.activeCatalog()
    local photos = catalog:getTargetPhotos()

    if #photos ~= 1 then
        error("Select exactly one photo for the Lightroom multipart probe")
    end

    local photo = photos[1]
    local photoUuid = photo:getRawMetadata("uuid")

    if photoUuid ~= selection.photoUuid then
        error("Select the verified public test photo " .. selection.sourceFilename)
    end

    local confirmation = LrDialogs.confirm(
        "Run direct Flickr upload probe?",
        string.format(
            "This photo was independently verified as public on Flickr. Lightroom will render a temporary "
                .. "full-resolution 8-bit sRGB PNG, request one upload signature from the loopback signer, "
                .. "and create one private, search-hidden duplicate.\n\nSource: %s\nPublic page: %s\n\n"
                .. "Start the signer before continuing.",
            selection.sourceFilename,
            selection.publicFlickrUrl
        ),
        "Upload Privately",
        "Cancel"
    )

    if confirmation ~= "ok" then
        return
    end

    local runDirectory = createRunDirectory(photoUuid)
    local renderedPath = nil
    context:addCleanupHandler(function()
        if
            renderedPath
            and LrPathUtils.parent(renderedPath) == runDirectory
            and LrFileUtils.exists(renderedPath) == "file"
        then
            LrFileUtils.delete(renderedPath)
        end
    end)

    renderedPath = renderPhoto(context, photo, runDirectory)
    local envelope = requestSigningEnvelope()
    local flickrPhotoId = uploadPng(context, renderedPath, envelope)
    LrDialogs.message(
        "FGA Lightroom multipart probe passed",
        "Flickr accepted the direct Lightroom upload.\n\nFlickr photo ID: " .. flickrPhotoId,
        "info"
    )
end

return DirectUploadProbe
