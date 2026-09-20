# Keep the localization extension in this project while retaining the pinned
# libultraship submodule revision. Reconfiguration must be idempotent.
function(apply_lus_ui_translation source_dir)
    find_package(Git REQUIRED)
    set(ui_patch "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/lus-ui-translation.patch")
    execute_process(
        COMMAND "${GIT_EXECUTABLE}" apply --check "${ui_patch}"
        WORKING_DIRECTORY "${source_dir}"
        RESULT_VARIABLE can_apply OUTPUT_QUIET ERROR_VARIABLE apply_error)
    if(can_apply EQUAL 0)
        execute_process(
            COMMAND "${GIT_EXECUTABLE}" apply "${ui_patch}"
            WORKING_DIRECTORY "${source_dir}"
            RESULT_VARIABLE applied OUTPUT_QUIET ERROR_VARIABLE apply_error)
        if(NOT applied EQUAL 0)
            message(FATAL_ERROR "Unable to apply LUS menu translations: ${apply_error}")
        endif()
    else()
        execute_process(
            COMMAND "${GIT_EXECUTABLE}" apply --reverse --check "${ui_patch}"
            WORKING_DIRECTORY "${source_dir}"
            RESULT_VARIABLE already_applied OUTPUT_QUIET ERROR_QUIET)
        if(NOT already_applied EQUAL 0)
            message(FATAL_ERROR "LUS UI sources no longer match the localization patch. Review the submodule update. ${apply_error}")
        endif()
    endif()
endfunction()

if(DEFINED SOH_LUS_UI_SOURCE_DIR)
    apply_lus_ui_translation("${SOH_LUS_UI_SOURCE_DIR}")
endif()
