# Treatment Resistant Depression Database Command Line Interface

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

This allows us to query REDCap for the `id` and link it to the internal `study_id`.
This in turn allows us to identify whether a participant is already in the database.

### Other questionnaires

Any other data that we want to store, e.g. the answers to all questionnaires, should be stored in other instruments.
E.g. we'll want to create an instrument to hold the sharable demographic data, one for the PHQ9, etc.

Shared data instruments should have field names prefixed by the instrument name,
e.g. `demographics_age_int`, `phq9_1_interest_int`, etc.

Fields that record information but _do not appear in the questionnaire_ should use `meta` as their question number:
`phq9_meta_datetime_datetime`.

All instruments should have a `datetime_datetime` field to record when the data was collected.

None of the fields should include validation rules because we're passing data from True Colours,
which has already validated it.
Everything is saved as a string, and researchers will have to handle type conversion in their own code.
We can help by appending the field name with `_[type]` to indicate the type of the data.

#### Scores

Scores are calculated in True Colours and should be recorded in the database.
For each category that is scored, its value should be stored as `[name]_score_[category_name]_[type]`.
E.g. `phq9_score_total_int`.

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
