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

1. Make sure you have all the questionnaires you need in your test dataset (`tests/fixtures/*.csv`).
2. Run `tests/fixtures/tc_to_fixture.py`.
3. Open the `tests/fixtures/rc_variables.txt` file created by the script.

The `rc_variables.txt` file will look like this:

```text
###### instrument_name ######
field_1_name
field_2_name
field_3_name
...
```

4. For each line with `######` at the start and end, create an instrument with the fields listed below it.

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
