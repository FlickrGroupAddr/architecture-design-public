local LrApplication = import("LrApplication")
local LrDate = import("LrDate")
local LrDialogs = import("LrDialogs")
local LrExportSession = import("LrExportSession")
local LrFileUtils = import("LrFileUtils")
local LrPathUtils = import("LrPathUtils")
local LrProgressScope = import("LrProgressScope")

local Json = require("dkjson")

local PngMatrix = {}

local VARIANTS = {
    {
        id = "png-8-srgb",
        format = "PNG",
        bitDepth = 8,
        colorSpace = "sRGB",
    },
    {
        id = "png-8-adobergb",
        format = "PNG",
        bitDepth = 8,
        colorSpace = "AdobeRGB",
    },
    {
        id = "png-8-prophoto",
        format = "PNG",
        bitDepth = 8,
        colorSpace = "ProPhotoRGB",
    },
    {
        id = "png-16-srgb",
        format = "PNG",
        bitDepth = 16,
        colorSpace = "sRGB",
    },
    {
        id = "png-16-adobergb",
        format = "PNG",
        bitDepth = 16,
        colorSpace = "AdobeRGB",
    },
    {
        id = "png-16-prophoto",
        format = "PNG",
        bitDepth = 16,
        colorSpace = "ProPhotoRGB",
    },
    {
        id = "jpeg-q100-srgb",
        format = "JPEG",
        quality = 1,
        colorSpace = "sRGB",
    },
}

local function copyTable(source)
    local result = {}

    for key, value in pairs(source) do
        result[key] = value
    end

    return result
end

local function exportSettings(outputDirectory, variant)
    local settings = {
        LR_collisionHandling = "overwrite",
        LR_export_colorSpace = variant.colorSpace,
        LR_export_destinationPathPrefix = outputDirectory,
        LR_export_destinationType = "specificFolder",
        LR_export_postProcessing = "doNothing",
        LR_export_useParentFolder = false,
        LR_export_useSubfolder = false,
        LR_extensionCase = "lowercase",
        LR_format = variant.format,
        LR_outputSharpeningOn = false,
        LR_renamingTokensOn = false,
        LR_size_doConstrain = false,
        LR_useWatermark = false,
    }

    if variant.format == "PNG" then
        settings.LR_export_bitDepth = variant.bitDepth
        settings.LR_png_interlaced = false
    else
        settings.LR_jpeg_quality = variant.quality
    end

    return settings
end

local function chooseOutputDirectory()
    local paths = LrDialogs.runOpenPanel({
        title = "Choose a parent folder for the FGA test output",
        prompt = "Choose",
        canChooseFiles = false,
        canChooseDirectories = true,
        canCreateDirectories = true,
        allowsMultipleSelection = false,
    })

    return paths and paths[1] or nil
end

local function sourceRecord(photo)
    local sourcePath = photo:getRawMetadata("path")

    return {
        path = sourcePath,
        fileName = sourcePath and LrPathUtils.leafName(sourcePath) or nil,
        uuid = photo:getRawMetadata("uuid"),
        fileSizeBytes = photo:getRawMetadata("fileSize"),
        dimensions = photo:getRawMetadata("dimensions"),
        croppedDimensions = photo:getRawMetadata("croppedDimensions"),
        iso = photo:getRawMetadata("isoSpeedRating"),
    }
end

local function writeManifest(path, manifest)
    local file, message = io.open(path, "wb")

    if not file then
        error("Could not create manifest: " .. tostring(message))
    end

    local ok, writeMessage = file:write(Json.encode(manifest, { indent = true }) .. "\n")
    file:close()

    if not ok then
        error("Could not write manifest: " .. tostring(writeMessage))
    end
end

local function renderVariant(photos, runDirectory, variant, manifest, progress, completed, total)
    local variantDirectory = LrPathUtils.child(runDirectory, variant.id)
    local created, createMessage = LrFileUtils.createAllDirectories(variantDirectory)

    if not created then
        error("Could not create output directory: " .. tostring(createMessage))
    end

    local session = LrExportSession({
        photosToExport = photos,
        exportSettings = exportSettings(variantDirectory, variant),
    })

    for _, rendition in session:renditions({
        progressScope = progress,
        stopIfCanceled = true,
    }) do
        if progress:isCanceled() then
            return completed, true
        end

        local source = sourceRecord(rendition.photo)
        progress:setCaption("Rendering " .. variant.id .. ": " .. (source.fileName or "photo"))
        local startedAt = LrDate.currentTime()
        local success, pathOrMessage = rendition:waitForRender()
        local endedAt = LrDate.currentTime()
        local record = {
            variant = variant.id,
            source = source,
            startedAt = LrDate.timeToW3CDate(startedAt),
            finishedAt = LrDate.timeToW3CDate(endedAt),
            durationSeconds = endedAt - startedAt,
            success = success,
        }

        if success then
            local attributes = LrFileUtils.fileAttributes(pathOrMessage)
            record.outputPath = pathOrMessage
            record.fileSizeBytes = attributes and attributes.fileSize or nil
        else
            record.error = pathOrMessage
        end

        manifest.renders[#manifest.renders + 1] = record
        completed = completed + 1
        progress:setPortionComplete(completed, total)
    end

    return completed, false
end

local function describeVariants()
    local names = {}

    for _, variant in ipairs(VARIANTS) do
        names[#names + 1] = variant.id
    end

    return table.concat(names, ", ")
end


function PngMatrix.run(context)
    local catalog = LrApplication.activeCatalog()
    local photos = catalog:getTargetPhotos()

    if #photos == 0 then
        LrDialogs.message("No photos selected", "Select one or more photos and run the command again.", "warning")
        return
    end

    local outputParent = chooseOutputDirectory()

    if not outputParent then
        return
    end

    local outputCount = #photos * #VARIANTS
    local confirmation = LrDialogs.confirm(
        "Run FGA PNG test matrix?",
        string.format(
            "%d selected photo(s) × %d variants = %d full-resolution exports.\n\nVariants: %s\n\n"
                .. "This can take a long time and consume several gigabytes.",
            #photos,
            #VARIANTS,
            outputCount,
            describeVariants()
        ),
        "Run Matrix",
        "Cancel"
    )

    if confirmation ~= "ok" then
        return
    end

    local startedAt = LrDate.currentTime()
    local runName = "fga-png-matrix-" .. LrDate.timeToUserFormat(startedAt, "%Y%m%d-%H%M%S", false)
    local runDirectory = LrPathUtils.child(outputParent, runName)
    local created, createMessage = LrFileUtils.createAllDirectories(runDirectory)

    if not created then
        error("Could not create run directory: " .. tostring(createMessage))
    end

    local manifest = {
        schemaVersion = 1,
        pluginVersion = "0.2.0",
        startedAt = LrDate.timeToW3CDate(startedAt),
        runDirectory = runDirectory,
        selectedPhotoCount = #photos,
        variants = {},
        renders = {},
        canceled = false,
    }

    for _, variant in ipairs(VARIANTS) do
        manifest.variants[#manifest.variants + 1] = copyTable(variant)
    end

    local progress = LrProgressScope({
        title = "FGA PNG test matrix",
        functionContext = context,
    })
    progress:setCancelable(true)

    local completed = 0

    for _, variant in ipairs(VARIANTS) do
        local canceled
        completed, canceled = renderVariant(
            photos,
            runDirectory,
            variant,
            manifest,
            progress,
            completed,
            outputCount
        )

        if canceled then
            manifest.canceled = true
            break
        end
    end

    manifest.finishedAt = LrDate.timeToW3CDate(LrDate.currentTime())
    manifest.completedRenderCount = completed
    local manifestPath = LrPathUtils.child(runDirectory, "manifest.json")
    writeManifest(manifestPath, manifest)
    progress:done()

    local title = manifest.canceled and "FGA PNG matrix canceled" or "FGA PNG matrix complete"
    LrDialogs.message(
        title,
        string.format("Recorded %d of %d render(s).\n\nManifest: %s", completed, outputCount, manifestPath),
        manifest.canceled and "warning" or "info"
    )
end

return PngMatrix
