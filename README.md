# myfr24-converter
This is a command-line tool to convert "App in the Air" data export to a csv format accepted by MyFlightradar24. 
It's built mainly for one-time migration of your flight history from "App in the Air" to MyFlightradar24.

## How to use

### Step 1: Export "App in the Air" data

In the "App in the Air" app: **Profile | Settings | Export account**.

You will then receinve *an email* containing your full data export in a file named `data.txt`. 
This is the file you will then need to pass to the converter script as an input.

### Step 2: Run the converter script

Run the script from within the top-level project folder 
(or provide a qualified path to the `data` folder in a `--data-dir` argument)

```shell
python converter.py --input <PATH_TO_DATA_TXT> --output <PATH_TO_OUTPUT_CSV>
```

### Step 3: Upload the result to MyFlightradar24

Upload the converter's output to https://my.flightradar24.com/settings/import

## Limitations and quirks

Despite claiming to accept Openflights.org export format, MyFlightradar24 doesn't always correctly recognize 
the airline and the aircraft model from the openflights export. 

Surprisingly, MyFlightradar24 doesn't accept IATA/ICAO codes for airlines/planes, but rather relies on internal ids 
or full names. 
On top of that, their internal ids don't match with the openflights database, and are not easily accessible.

Full names in the openflights db *mostly* match MyFR24's expected names, but not always.
For the relatively rare occasion of the mismatch, manually created `data/extra_airlines.dat` and `data/extra_planes.dat` 
provide overrides or additions to the openflights db 
(openflights database is no longer regularly updated, so new airlines are missing).
These files are by no means exhaustive, and your export will probably contain a few mismatched airlines or planes. If
you notice a large amount of missing records in your MyFR24 flight import please consider adding to the override files.
(The expected names for airlines/planes on MyFR24 can be found in the suggestion box when manually adding a flight).

Some known issues:

* Boeing 737 MAX cannot be added to MyFR24. I was unable to find the right spelling that would be recognized by the import script
* Wrong airline name can be picked in case of an IATA code conflict. 2-letter IATA codes are not unique worldwide, however
"App in the Air" uses them as the only airline identifier in the data export. The coverter doesn't check whether a flight
actually exists and would pick the *last* matching airline in the openflights database. 
* The script ignores `Ownership.MINE` and `Ownership.NOT_MINE` flags and adds all the flights to the output regardless

## Acknowledgments

As a first step in its execution, the script will download airlines 
and planes databases provided by [Openflights](https://openflights.org/data.html).

We are very thankful to OpenFlights for maintaining and publishing the data.

