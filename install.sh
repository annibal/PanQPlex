#!/usr/bin/env bash
set -uoe pipefail

# clickable links in modern terminals (OSC-8)
echolink(){ echo -e "\e]8;;$1\a$2\e]8;;\a"; }
say(){ echo -e "⟫ $*"; }
die(){ echo -e "⟫ ERROR: $*" >&2; exit 1; }

say "PanQPlex installation";

# --- repo root sanity
need=(pyproject.toml src/n2bl/cli.py requirements.txt)
missing=(); for f in "${need[@]}"; do [[ -f "$f" ]] || missing+=("$f"); done
((${#missing[@]}==0)) || die "run from repo root; missing: ${missing[*]}"

say "Installing PanQPlex\nMODE: DEV\nPATH: $(pwd)\n"

# --- prerequisites
qtdMissingDeps=0;
logNameStr=" "
logArgsStr=" "
logStr=" "
if [[ !$(command -v jq) ]]; then
  qtdMissingDeps = $qtdMissingDeps + 1
  logNameStr="$logNameStr '$(echolink "https://stedolan.github.io/jq/download/" "jq (jqlang)")'";
  logArgsStr="$logArgsStr jq";
fi
if [[ !$(command -v python3-venv) ]]; then
  qtdMissingDeps = $(($qtdMissingDeps + 1))
  logNameStr="$logNameStr '$(echolink "https://www.python.org/" "python3-venv")'";
  logArgsStr="$logArgsStr python3-venv";
fi



if [[ $isMissingDeps ]]; then
  logStr="The program"
  [[ $isMissingDeps == true ]] && logStr="${logStr}s";
  logStr="${logStr} $( echo [[ $isMissingDeps == true ]] && "are" || "is" ) required.\n";
  logStr="${logStr}To install $( [[ $isMissingDeps == true ]] && "them" || "it" ), "
  logStr="${logStr}try running this command:\n  sudo apt install $logArgsStr\n\n";

  die $logStr;
fi

# --- python env
say "setting up python virtual environment";
[[ -d .venv ]] || python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

say "installation script will install more scripts to install another script";
say "running 'pip install setuptools wheel':";
pip install -q -U pip setuptools wheel
pip install -q -e .

say "setting up credentials";
# --- config/creds paths
CONF="${XDG_CONFIG_HOME:-$HOME/.config}/n2bl"
mkdir -p "$CONF"
CREDS="$CONF/client_secret.json"
say "   "
say "  This is the credentials file path: '$CREDS'";
say "  You'll have to put your project's api keys there";
say "  otherwise this script can't do the OAuth.";
say "   "

TOKEN="$CONF/token.pickle"
say "   "
say "  After your first successful OAuth, the token file will store the login data.";
say "  If the token file isn't there, or it's data has expired, PanQPlex will ask you for OAuth again.";
say "   "

say "checking credentials data";
# --- write template if missing/invalid
valid_json(){ jq -e '.installed.client_id and .installed.client_secret and (.installed.redirect_uris|length>0)' "$1" >/dev/null 2>&1; }

if [[ ! -s "$CREDS" ]] || ! valid_json "$CREDS"; then
  if [[ ! -s "$CREDS" ]]; then
    say "Creating credentials file '$CREDS'";
  fi;
  if ! valid_json "$CREDS"; then
    say "Invalid content in '$CREDS'. Replacing with template.";
  fi
  cat >"$CREDS" <<'JSON'
{
  "installed": {
    "client_id": "",
    "project_id": "",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "",
    "redirect_uris": ["http://localhost"]
  }
}
JSON
fi

# --- if secrets missing, print your 10-step guide (with links)
need_vals=$(jq -r '.installed | [.client_id,.project_id,.client_secret] | map(length>0) | all' "$CREDS") || need_vals=false
if [[ "$need_vals" != true ]]; then
  say "\n\nOAuth setup required. Follow these steps:\n"
  say " 1. Open $(echolink "https://console.cloud.google.com" "Google Cloud Console") and log in."
  say " 2. Create/select a GCP project."
  say " 3. Go to $(echolink "https://console.cloud.google.com/apis/library" "API Library"); search for “YouTube Data API v3”."
  say "    Direct search: $(echolink "https://console.cloud.google.com/apis/library?q=YouTube%20Data%20API%20v3" "link")."
  say " 4. Open $(echolink "https://console.cloud.google.com/apis/library/youtube.googleapis.com" "YouTube Data API v3") and click **Enable**."
  say "    Check enabled APIs at $(echolink "https://console.cloud.google.com/apis/dashboard" "APIs & Services → Dashboard")."
  say " 5. Open the API’s project instance page: $(echolink "https://console.cloud.google.com/apis/api/youtube.googleapis.com/metrics" "Metrics")."
  say "    Click the **Credentials** tab (or go to $(echolink "https://console.cloud.google.com/apis/api/youtube.googleapis.com/credentials" "this link"))."
  say " 6. Click **Create Credentials** (top-right) → **OAuth client ID**."
  say " 7. Choose **Desktop app**, name it, create."
  say " 8. A popup appears with your client. Click **Download JSON**."
  say " 9. Save that file as: $CREDS  (or copy its fields into that file)."
  say "10. Reactivate venv and run a command to trigger OAuth (URL will print):"
  say "      source .venv/bin/activate && pqp list-channels\n"
fi

# --- force fresh OAuth (safe)
say "removing pickle to refresh credentials";
rm -f "$TOKEN"

# --- smoke test
if ! .venv/bin/pqp -h >/dev/null 2>&1; then
  die "PanQPlex entry point missing; check pyproject.toml [project.scripts] pqp = \"n2bl.cli:main\" then: pip install -e ."
fi

say "OK.\nNext:\n  source .venv/bin/activate\n  pqp -h\n  pqp scan\n"


# if the json inside `~/.panqplex/n2bl/credentials` is missing the values for `client_id`, `project_id`, or `client_secret`, output the following:

  # echo -e "\n\n  1. Open $(echolink "https://console.cloud.google.com" "Google Cloud Console") in your browser, and log in to your account in there;";

  # echo -e "\n\n  2. Create a new project (or if you already have a project you like, feel free to use it), then select the project;";

  # echo -e "\n\n  3. Go the the $(echolink "https://console.cloud.google.com/apis/library" "API Library page") then search for the "Youtube Data API v3" api ( $(echolink "https://console.cloud.google.com/apis/libraryq=Youtube%20Data%20API%20v3" "Link straight to search results") )";
  # echo -e "\n     The APIs in this page will lead you to the global information about the API.";

  # echo -e "\n\n  4. Once the $(echolink "https://console.cloud.google.com/apis/library/youtube.googleapis.com" "Youtube Data API v3") is found, click the  'enable' button. This will activate the API into your project."
  # echo -e "\n     To view all the APIs enabled in your project, go to the $(echolink "https://console.cloud.google.com/apis/dashboard" "APIs & Services Dashboard").";
  # echo -e "\n     The newly enabled API should be listed in the bottom of the table;";

  # echo -e "\n\n  5. Go to the $(echolink "https://console.cloud.google.com/apis/api/youtube.googleapis.com/metrics" "Youtube Data API v3 instance page") - it's the project's enabled API page, with metrics. Not the previous, global API information page.";
  # echo -e "\n     Here you'll find three tabs a bit beneath the title: 'Metrics", 'Quotas and System Limits', and 'Credentials'. Click the 'Credentials' tab, you'll go to the $(echolink "https://console.cloud.google.com/apis/api/youtube.googleapis.com/credentials" "API instance's Credentials page").";

  # echo -e "\n\n  6. In the same height as the three Tabs, but located in the far right side of the page, click the 'Create Credentials' button. It should reveal a menu - select 'OAuth client ID'.";

  # echo -e "\n\n  7. You'll be redirected to the $(echolink "https://console.cloud.google.com/auth/clients/create" "OAuth Client ID creation page"), for Youtube Data API v3. Choose the option 'Desktop App' on the dropdown.";

  # echo -e "\n\n  8. Give it a name and submit the form - immediately after that, GCP will pop up a dialog (important) about your project's youtube data v3 API.""
  # echo -e "\n      This popup lets you download and/or copy the brand new credentials for the API. I strongly recommend downloading them, since this popup will never show up again,";
  # echo -e "\n      Click the 'Download JSON' button;";

  # echo -e "\n\n  9. This downloaded file contains the secret API keys that permit logging in via OAuth.";
  # echo -e "\n      Be careful to do not leak it.";
  # echo -e "\n      PanQPlex expects this file to be at '~/.panqplex/n2bl/', under the file name 'credentials.json', with a valid JSON content.";
  # echo -e "\n      This installer creates it at '$HOME/.panqplex/n2bl/credentials.json', and filled the common fields.";
  # echo -e "\n      After obtaining the 'client_secret_1234...googleusercontent.com.json' file from GCP, the last step is to fill the remaining secret fields from '.panqplex/n2bl/credentials.json'.";
  # echo -e "\n      Or feel free to simply cut the downloaded file and paste it overwriting the '.panqplex/n2bl/credentials.json' file, it will work as well.";
 
  # echo -e "\n\n 10. Lastly, this installer has already created the python virtual environment (.venv) and is inside it, so simply run 'pqp -h' or any other command.";
  # echo -e "\n      PanQPlex will do the OAuth flow on it's first run, and will output an URL for you."
  # echo -e "\n      Follow the URL on your browser, whichever one that you have an Google or YouTube account. Authorize PanQPlex in the browser once for PanQPlex to work.";
  # echo "\n\n░░░░░░░░░░░░░░░░░░░░\n"


