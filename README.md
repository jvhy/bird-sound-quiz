# Bird Sound Quiz

Bird sound identification game built with Django 🐦


## 📦 Installation

This project is managed via [uv](https://docs.astral.sh/uv/). It is not strictly required, but recommended.

1. Clone the repository:
```bash
$ git clone git@github.com:jvhy/bird-sound-quiz.git
```

2. Create a virtual environment in `.venv`:
```bash
$ uv venv
```

3. Install dependencies:
```bash
$ uv sync --group postgres  # or --group mysql
```


## ⚙️ Configuration

This section describes an example configuration for running the app for development purposes.

1. Have a database server of your choice (PostgreSQL or MySQL) installed and running, create a database and set a user + password.

2. Create a `.env` file with the following keys:
```
DATABASE_BACKEND=postgresql  # or mysql
DATABASE_NAME=my_db_name
DATABASE_USER=my_db_user
DATABASE_PASSWORD=my_db_pw
DATABASE_PORT=5432           # 3306 for mysql default
DATABASE_HOST=localhost
```

## ⬇️ Importing data

There are five custom commands for populating the database and downloading app media from different external sources. These commands use extra dependencies that can be installed via `uv`:
```bash
$ uv sync --group postgres --group import
```

### External APIs
#### eBird

Database tables for species, regions and observations can be populated with data from the [eBird](https://ebird.org/home). This requires and API key that can be obtained by visiting https://ebird.org/api/keygen. API documentation can be found [here](https://documenter.getpostman.com/view/664302/S1ENwy59).

To use commands that import data from the eBird API, add the following line to `.env`:
```
EBIRD_API_KEY=<your API key>
```

#### laji.fi

Species data can be alternatively imported from [laji.fi](https://laji.fi). An API access token is required: see instructions for obtaining one here: https://laji.fi/about/3120. API documentation can be found [here](https://api.laji.fi/explorer/).

To use commands that import data from the laji.fi API, add the following line to `.env`:
```
LAJIFI_API_TOKEN=<your API token>
```

**NOTE**: It is highly recommended to use eBird instead of laji.fi for species information, as the observation table populating command relies on eBird species codes. If laji.fi is used for species information, the observation table needs to be populated manually.

#### xeno-canto

Recording metadata and audio files can be downloaded from [xeno-canto](https://xeno-canto.org). This requires an API key that can be obtained by registering an account on xeno-canto and visiting https://xeno-canto.org/account.

To use commands that import data from the xeno-cano API, add the following line to `.env`:
```
XENOCANTO_API_KEY=<your API key>
```

### Import commands

The five custom management commands for data importing are:

1. `populate_species_table` - Imports species data from eBird or laji.fi
2. `populate_region_table` - Imports region data from eBird
3. `populate_observation_table` - Imports observation data from eBird. Requires data in species and region tables.
4. `populate_recording_table` - Imports recording metadata from xeno-canto. Requires data in species, region and observation tables.
5. `download_audio` - (Optional) Downloads audio files from xeno-canto to disk. Requires data in recording table.

The commands are used via `manage.py`:

1. Ensure that database migrations are up to date (only needs to be ran once):
```bash
$ uv run manage.py migrate
```

2. Run an import command, for example:
```bash
$ uv run manage.py populate_species_table
```

&ensp;&ensp;&ensp;&ensp;To see the arguments for a command:
```bash
$ uv run manage.py <command> --help
```

&ensp;&ensp;&ensp;&ensp;You can also use the `populate_db` recipe in the `Makefile`. This will import data for Finnish species by default:
```bash
$ make populate_db
```


#### (Optional) Downloading audio files

Audio files can be downloaded locally via the `download_audio` custom command. Note that this is entirely optional (and not recommended): by default, the app will use audio files hosted by xeno-canto.

To use locally hosted audio files:

0. (Populate all db tables via custom commands described above)
1. Run audio download command. Downloaded audio files are saved to `media/audio/`:
```bash
$ uv run manage.py download_audio
```
2. If some downloads fail, the command will prompt you to drop recording rows with failed downloads. **It's recommended to do so.**
3. Set option to enable local audio file hosting in `.env`:
```
SELF_HOST_AUDIO=true
```


## 🚀 Run


### Development

To launch a development server, use `manage.py`:

```bash
$ uv run manage.py runserver
```

Or use `make` recipe:
```bash
$ make serve  # equivalent to the above command
```


### Production

TBA
