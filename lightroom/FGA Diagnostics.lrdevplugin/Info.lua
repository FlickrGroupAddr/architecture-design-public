return {
    LrSdkVersion = 15.0,
    LrSdkMinimumVersion = 15.0,
    LrToolkitIdentifier = "org.fga.lightroom.diagnostics",
    LrPluginName = LOC("$$$/FGA/Diagnostics/PluginName=FGA Diagnostics"),

    LrExportServiceProvider = {
        title = LOC("$$$/FGA/Diagnostics/CatalogAssociationProvider=FGA Catalog Association Probe"),
        file = "CatalogAssociationPublishServiceProvider.lua",
    },

    LrLibraryMenuItems = {
        {
            title = LOC("$$$/FGA/Diagnostics/RunPngMatrix=Run PNG Test Matrix on Selected Photos"),
            file = "RunPngMatrix.lua",
        },
        {
            title = LOC("$$$/FGA/Diagnostics/RunDirectUploadProbe=Test Direct Flickr Upload from Public Photo"),
            file = "RunDirectUploadProbe.lua",
        },
        {
            title = LOC("$$$/FGA/Diagnostics/RunExistingPhotoSelectorProbe=Test Existing Public Photo Selector"),
            file = "RunExistingPhotoSelectorProbe.lua",
        },
        {
            title = LOC("$$$/FGA/Diagnostics/PrepareCatalogAssociation=0067: Prepare Disposable Catalog Fixture"),
            file = "RunPrepareCatalogAssociationProbe.lua",
        },
        {
            title = LOC("$$$/FGA/Diagnostics/CreateCatalogAssociation=0067: Create Catalog-Only Association"),
            file = "RunCreateCatalogAssociationProbe.lua",
        },
        {
            title = LOC("$$$/FGA/Diagnostics/InspectCatalogAssociation=0067: Inspect Catalog Associations"),
            file = "RunInspectCatalogAssociationProbe.lua",
        },
        {
            title = LOC("$$$/FGA/Diagnostics/RemoveCatalogAssociation=0067: Remove Catalog-Only Association"),
            file = "RunRemoveCatalogAssociationProbe.lua",
        },
    },

    VERSION = {
        major = 0,
        minor = 4,
        revision = 0,
        build = 10,
    },
}
