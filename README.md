# Treatment Resistant Depression Database Command Line Interface

[![.github/workflows/test.yml](https://github.com/OxfordRSE/trd-cli/actions/workflows/test.yml/badge.svg)](https://github.com/OxfordRSE/trd-cli/actions/workflows/test.yml)
[![codecov](https://codecov.io/github/OxfordRSE/trd-cli/graph/badge.svg?token=myj04HCbDQ)](https://codecov.io/github/OxfordRSE/trd-cli)

This CLI performs automated data collection and curation for the TRD Database project.

## Deployment

The tool is deployed to ECS on AWS by deploying it as a `docker` container.
The `Dockerfile` is included in the repository.

The AWS systems are set up using `terraform` and the configuration is included in the `.tf` files.
The core setup is in the `aws.tf` file.

Variables are declared in the `variables.tf` file, and their actual values are exported in `secret.tfvars`.
The contents of `secret.tfvars` are not included in the repository.

`secrets.tfvars` should be created in the root directory of the repository and should contain the following variables:
```
# secrets.tfvars

redcap_secret        = "your_redcap_secret_value"
true_colours_secret  = "your_true_colours_secret_value"
mailgun_secret       = "your_mailgun_secret_value"
```

## REDCap setup

The project converts True Colours data to REDCap data.
REDCap doesn't allow direct database access, however, so we need to create fake instruments in REDCap to store the data.


### The quick way

The quick way to set up the REDCap project is still quite slow, but it's faster than the long way.

#### Generate a list of variables

Run `python trd_cli.py export_redcap_structure -o rc_variables.txt` to export the variables from the True Colours data.
This will output a file called `rc_variables.txt` in the current directory.
It will contain the names of the instruments and all the fields that will be exported for those instruments for 
all the questionnaires the tool knows about.

The `rc_variables.txt` file will look like this:

```text
###### instrument_name ######
field_1_name
field_2_name
field_3_name
...
```

#### Create the instruments in REDCap

For each line with `######` at the start and end, create an instrument with the fields listed below it.

You should use `instrument_name` as the name of the instrument in REDCap, although this is not strictly necessary.
The field names must be copied exactly as they appear in the file.
This means that most will be prefixed with their instrument name (except for private fields).

Each field will have to be created in REDCap with the following settings:
- Field Type: Text Box (Short Text, Number, Date/Time...)
- Field Label: The name of the field in the file (not strictly necessary, but it helps)
- Variable Name: The name of the field in the file (**exactly as it appears in the file**)
- Identifier: No (unless it's an `id` field e.g. `instrument_name_response_id`)
- _No required, validation, etc_ (we're importing from True Colours, so we don't want stuff to break because of REDCap's validation)

When the data are exported from REDCap, the field names will help identify which instrument they belong to.

### The long way

Create a `private` instrument in REDCap with Text Box fields with these Variable Names:

| Field Name         | True Colours `patient.csv` field | Contains personal information? |
|--------------------|----------------------------------|--------------------------------|
| `id`               | `id`                             | `False`                        |
| `nhsnumber`        | `nhsnumber`                      | `True`                         |
| `birthdate`        | `birthdate`                      | `True`                         |
| `contactemail`     | `contactemail`                   | `True`                         |
| `mobilenumber`     | `mobilenumber`                   | `True`                         |
| `firstname`        | `firstname`                      | `True`                         |
| `lastname`         | `lastname`                       | `True`                         |
| `preferredcontact` | `preferredcontact`               | `False`                        |

The `id` _must_ be listed with 'Identifier' set to 'No'.
This allows us to query REDCap for the `id` and link it to the internal `study_id`.
This in turn allows us to identify whether a participant is already in the database.

#### Instruments for other questionnaires

The instruments only exist as a framework for holding data exported from True Colours. 
This means that we need to provide a very specific structure:

- Use the scale code as a prefix, and include item number (where applicable), item short description, and data type
  - E.g. `demo_age_int` or `phq9_1_interest_float`
- Include a `datetime` field for each instrument to hold the time of completion
  - E.g. `phq9_datetime`
  - (the 'datetime' is assumed from the name, and the format is going to be True Colours rather than REDCap)
- Include `_score_` fields for any scores or subscale scores that are calculated in True Colours
  - E.g. `phq9_score_total_float`

## Using the REDCap data

### We save **scores** only

The data in REDCap are the **scores** for items on questionnaires. 
This means that reverse-coded items, etc. are already accounted for.

To recover the actual answers that a participant entered, refer to the data dictionary for the scale of interest.

### Handling exported data

REDCap records are always exported in `string` format. 
This means that the data may have to be parsed to be useful.
The last part of the name of field in a record is an indication of the data type to which it should be converted.
These types come from True Colours, and their sanity can be checked with reference to the data dictionary for the relevant scale.

REDCap structures the data for repeated instruments such that all potential rows are returned,
even if their values are not relevant. 
E.g. given (for brevity) we just have `demo` and `phq9` instruments, the first completion of `demo` be a record like:
```json
{
  "study_id": "REDCap assigned identifier",
  "redcap_repeat_instrument": "demo",
  "redcap_repeat_instance": 1,
  "demo_datetime": "20241105 15:31",
  "demo_gender_int": "1",
  "demo_other_fields": "other fields and content",
  "demo_complete": "2 indicates complete, 1 incomplete; presumably 0 not started?",
  "phq9_datetime": "",
  "phq9_1_interest_float": "",
  "phq9_other_fields": "all these PHQ fields will be blank"
}
```

This is true _whether or not `phq9` has been completed first!_
Even if `phq9` has been completed, the values **will not** be included in the `demo` row. 
This does make sense.

**Note** that the `redcap_repeat_instance` field is actually an **integer** whereas everything else is a string.
There doesn't seem to be a way in REDCap to get it to store data values as anything but strings.

## Implementation (`QUESTIONNAIRES`)

The core work of the tool is performed by the `QUESTIONNAIRES` list in `conversions.py`.
This contains a dict for each questionnaire we expect to find in the True Colours data.
Below, you will find a description of each property and how it relates to True Colours questionnaire setup.

### `name`

Corresponds to the **Title** field in the True Colours Questionnaire Builder. 
It is _not the Name field_.

### `code`

This is the short questionnaire identifier used for REDCap. 
It does not relate to anything in True Colours. 
It should be short and clear.

Exported REDCap data will have fields named like `<code>_<#>_<item>_<data_type>` (e.g. `phq9_1_interest_float`), 
so expect whatever you put here to be visible to researchers in their datasets.

### `items`

The `items` is a list of the questions in the questionnaire. 
The **order of the items** is the order they are listed in the True Colours Questionnaire Builder. 
So the first item corresponds to Question 1, the second to Question 2, and so on.
The value is a string that will be used to add some context to the variable name for researchers.

Exported REDCap data will have fields named like `<code>_<#>_<item>_<data_type>` (e.g. `phq9_1_interest_float`), 
so picking a good name will help researchers interpret their datasets without constant reference to the data dictionary.
Names should be as short as possible.

### `scores`

These correspond to the **Category Name** fields of the **Questionnaire Scoring** in the 
True Colours Questionnaire Builder.
They must match exactly.

The score will be converted into lower case with spaces and other characters replaced with `-` or removed.

Exported REDCap data will have fields named like `<code>_score_<score>_<data_type>` (e.g. `phq9_score_total_float`).

### `conversion_fn`

This is the function used for converting the questionnaire from True Colours data into REDCap data.
There are several conversion functions listed in `conversions.py`.
For most questionnaires the one to use will be `convert_scores`, which extracts the scores for each question.

## Pre-commit

This repository uses `pre-commit` to enforce code quality standards.
To install `pre-commit`, run the following command:
```
pip install pre-commit
```

To install the pre-commit hooks, run the following command:
```
pre-commit install
```

### Hooks

The following hooks are used in this repository:
- `ruff` Python code formatter and linter
- `terraform` Terraform code formatter and linter
- a few of the `pre-commit` default hooks

## Citations

PyCap:
```
Burns, S. S., Browne, A., Davis, G. N., Rimrodt, S. L., & Cutting, L. E. PyCap (Version 1.0) [Computer Software].
Nashville, TN: Vanderbilt University and Philadelphia, PA: Childrens Hospital of Philadelphia.
Available from https://github.com/redcap-tools/PyCap. doi:10.5281/zenodo.9917
```
