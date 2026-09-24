import React from "react";
import { Autocomplete, TextField } from "@mui/material";

interface FieldAutocompleteProps {
  label: string;
  value: string | null;
  options: string[];
  onChange: (value: string | null) => void;
  disabled?: boolean;
  fullWidth?: boolean;
  helperText?: string;
}

/**
 * A "dropdown with option to add new" field: offers existing values as
 * suggestions (freeSolo Autocomplete) but also accepts any typed value
 * that isn't in the list yet. Saving that value is what makes it show up
 * as a suggestion for everyone else next time - the option list itself
 * lives on the server (GET /assets/field-options), not in this component.
 */
export default function FieldAutocomplete({
  label,
  value,
  options,
  onChange,
  disabled,
  fullWidth = true,
  helperText,
}: FieldAutocompleteProps) {
  return (
    <Autocomplete
      freeSolo
      disabled={disabled}
      fullWidth={fullWidth}
      options={options}
      value={value}
      onChange={(_event, newValue) => onChange((newValue as string) || null)}
      onInputChange={(event, newInputValue, reason) => {
        // Keep free-typed text in sync as the user types, but don't clear
        // the field just because the dropdown blurred without a selection.
        if (reason === "input") {
          onChange(newInputValue || null);
        }
      }}
      renderInput={(params) => (
        <TextField {...params} label={label} helperText={helperText} />
      )}
    />
  );
}
