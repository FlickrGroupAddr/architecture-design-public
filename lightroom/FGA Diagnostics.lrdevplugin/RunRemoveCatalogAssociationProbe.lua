local LrDialogs = import("LrDialogs")
local LrFunctionContext = import("LrFunctionContext")
local LrTasks = import("LrTasks")

local CatalogAssociationProbe = require("CatalogAssociationProbe")

LrTasks.startAsyncTask(function()
    LrFunctionContext.callWithContext("removeFgaCatalogAssociationProbe", function(context)
        LrDialogs.attachErrorDialogToFunctionContext(context)
        CatalogAssociationProbe.run("remove_association", CatalogAssociationProbe.removeAssociation)
    end)
end)
