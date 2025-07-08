# PanQPlex

Short for `Pankeimena QueuePlex Volitional Synchronization Framework`.

> Pan (all of, every) + Keinema (documents, files)
> Queue (waiting list) + Plex (has parts)

⇾ This is made of several queues of every file ever

> Volitional (relates to the use of one's will)
> Syn (together) + Chrono (time) + Ize (verb, ization)
> Frame (the structure of a construct) + Work (crafted from)
⇾ A built mechanism that makes a set of things be identical in 2+ places

Therefore, **PanQPlex** is a tool, made of one or more waiting lists of files, that makes all these existing files from a certain location be identical in other locations.

TL;DR: PanQPlex uploads several files to youtube automatically.

## Features

- YouTube (futurely more streaming platforms)
- Upload Throtte to prevent ban
- Multiple Accounts
- Metadata management
- Cool interface

## Usage

Using the abbreviated form, call upon the PanQPlex using the `pqpvsf` command.

PanQPlex works best when given a single folder with all the movies:

```bash
➜ user @ ~ cd movies

➜ user @ ~/movies ls
bigbuckbunny.webm   vid1.mp4   rec20250215.mov   vid_two.avi   what.mov   thirdvid.mkv
```

### Setup

Before all, PanQPlex needs some information about you. Run `pqpvsf` with the `--setup` flag to configure how the syncronization will happen:

> Currently only YouTube is available.
>
> Soon, when other platforms are supported, use the flag `--setup` followed by platform name to configure each one
>
> `--setup youtube` | `--setup vimeo` etc.

```bash
➜ user @ ~ pqpvsf --setup youtube

• API_KEY:
  12345gibberishgibberishgibberish654321

• MAX_DAILY_UPLOADS: 
  15

• DEFAULT_CHANNEL:
  7

PanQPlex setup completed!
```

You can define a custom path for the configuration file using the `--cfgpath` flag if you want to:

> The default path is `~/.pqpvsf/config-PLATFORM.env`

```bash
➜ user @ ~ pqpvsf --setup youtube --cfgpth ~/.pqpvsf/my-config-file.env
```

Use `--setup PLATFORM` together with the `--show` flag to view the current configuration:

```bash
➜ user @ ~ pqpvsf --setup --show

• API_KEY: 12345gibberishgibberishgibberish654321
• MAX_DAILY_UPLOADS: 15
• DEFAULT_CHANNEL: 7
```

### Multiple Users

First, assign an identifier for each user, mapping to it's API KEY:

```
USERS:
  Alice: 12345gibberishgibberishgibberish654321
  Bob: 567890gibberishgibberishgibberish567890
  Charles: 4htgfw4839570yt743yt34tc0345y85ty034jt
```

The default user will be the one configured in the API KEY in the configuration file.

Configure different settings for each user, such as rate limiting, after the USERNAME:API_KEY map in the configuration file:

```
[Alice]
  MAX_DAILY_UPLOADS: 3
  DEFAULT_CHANNEL: 1

[Charles]
  MAX_DAILY_UPLOADS: 52
```

Lastly, you can add an meta tag to specific files to override the automatic user choosing, and tie that file to an user.

Both the user name in the map, and an API_KEY can be set.

Using the API_KEY format allows configuring an user to an file without declaring that user in the config file, but later it will be a very difficult task trying to identify what user is assigned to each file.

```bash
pqpvsf file001.mov --set --key "PQP:user" --value "Charles"
pqpvsf file002.mov --set --key "PQP:user" --value "12345gibberishgibberishgibberish654321"
```

### Metadata Enriched Listing

PanQPlex can list the movies along with some or all relevant metadata:

Default list is a table with filename and information:

```bash
➜ user @ ~/movies pqpvsf --list
| UUID | STATUS  | TITLE                    | FILENAME         | LENGTH |     SIZE |     LASTUPDATE |
| ---- | ---- ➖ | ------------------------ | ---------------- | ------ | -------- | -------------- |
| FD29 | ✅ 100% | Big Buck Bunny           | bigbuckbunny.web |  10:35 | 180.0 MB |  1 mo. @ 16:07 |
| C222 | ✅ 100% | DCIM_250207_194133_01    | vid1.mp4         |   3:44 |  95.0 MB |  1 mo. @ 16:08 |
| C579 | 📤  73% | Recording made at Feb... | rec20250215.mo   |   0:06 |   8.0 MB |  2 mo. @ 04:40 |
| 79C9 | 🔜   0% | DCIM_250209_193358_02    | vid_two.av       |   3:21 |   1.5 GB |  2 mo. @ 15:50 |
| A34E | ⬆️  46% | DCIM_250211_200107_03    | thirdvid.mk      |   3:59 |  80.0 MB | 3 min. @ 20:32 |
| 36B2 | 🔄   0% | What?                    | what.mov         |  60:10 |   4.5 GB |   2 h. @ 18:22 |
```

Custom Columns:

```bash
➜ user @ ~/movies pqpvsf --list --columns UUID,STATUS,FILENAME
| UUID | STATUS  | FILENAME         |
| ---- | ---- ➖ | ---------------- |
| FD29 | ✅ 100% | bigbuckbunny.web |
| C222 | ✅ 100% | vid1.mp4         |
| C579 | 📤  73% | rec20250215.mo   |
| 79C9 | 🔜   0% | vid_two.av       |
| A34E | ⬆️  46% | thirdvid.mk      |
| 36B2 | 🔄   0% | what.mov         |
```

The listing can be filtered:

```bash
➜ user @ ~/movies pqpvsf --list --filter=status:queued
| UUID | 📋 STAT | TITLE                    | FILENAME         | LENGTH |     SIZE |    LAST UPDATE |
| 79C9 | 🔜   0% | DCIM_250209_193358_02    | vid_two.av       |   3:21 |   1.5 GB |  2 mo. @ 15:50 |
| 36B2 | 🔄   0% | What?                    | what.mov         |  60:10 |   4.5 GB |   2 h. @ 18:22 |
```

Alternate listing format, with more information, like Title and Description:

```bash
➜ user @ ~/movies pqpvsf --list=full

▶ bigbuckbunny.webm
  🆔 File ID: FD29     | Status: ✅ 100% - Synced
  🎞️ Length: 10:35     | ⚖️ Size: 180.0 MB
  ⭐ Created At: 2025-02-15 11:55      | 🗓️ Last Update: 1 mo. @ 16:07
  📜 Title: Big Buck Bunny
  📖 Desc: The first open source video published in blen...
  🏷️ 3d CreativeCommons Bunny

▶ vid1.mp4
  🆔 File ID: C222     | Status: ✅ 100% - Synced
  🎞️ Length: 3:44      | ⚖️ Size: 95.0 MB
  ⭐ Created At: 2025-02-07 19:41      | 🗓️ Last Update: 1 mo. @ 16:08
  📜 Title: DCIM_250207_194133_01
  📖 Desc: ␀
  🏷️ ␀

▶ rec20250215.mov
  🆔 File ID: C579     | Status: 📤 73% - Uploading
  🎞️ Length: 0:06      | ⚖️ Size: 8.0 MB
  ⭐ Created At: 2025-01-07 04:31      | 🗓️ Last Update: 2 mo. @ 04:40
  📜 Title: Recording made at February 15th, 2025
  📖 Desc: Nokia 3310
  🏷️ Recording Nokia 2210

▶ vid_two.avi
  🆔 File ID: 79C9     | Status: 🔜 0% - Queued
  🎞️ Length: 3:21      | ⚖️ Size: 1.5 GB
  ⭐ Created At: 2025-02-09 19:33      | 🗓️ Last Update: 2 mo. @ 15:50
  📜 Title: DCIM_250209_193358_02
  📖 Desc: ␀
  🏷️ ␀

▶ thirdvid.mkv
  🆔 File ID: A34E     | Status: ⏸️ 46% - Changed, Upload Paused
  ⬆️ 46% - Changed, Uploading
  🎞️ Length: 3:59      | ⚖️ Size: 82.3 MB
  ⭐ Created At: 2025-02-11 20:01      | 🗓️ Last Update: 3 min. @ 20:32
  📜 Title: DCIM_250211_200107_03
  📖 Desc: ␀
  🏷️ ␀

▶ what.mov
  🆔 File ID: 36B2     | Status: 🔄 0% - Changed, Queued
  🎞️ Length: 1:00:10   | ⚖️ Size: 4.5 GB
  ⭐ Created At: 2025-01-29 18:09      | 🗓️ Last Update: 2 h. @ 18:22
  📜 Title: What?
  📖 Desc: The What? Video
  🏷️ Fun Unexpected
```
Show information about a single file:

```bash
➜ user @ ~/movies pqpvsf ./rec20250215.mov

▶ rec20250215.mov
  🆔 File ID: C579     | Status: 📤 73% - Uploading
  🎞️ Length: 0:06      | ⚖️ Size: 8.0 MB
  ⭐ Created At: 2025-01-07 04:31      | 🗓️ Last Update: 2 mo. @ 04:40
  📜 Title: Recording made at February 15th, 2025
  📖 Desc: Nokia 3310
  🏷️ Recording Noki33210
```

### Synchronization

Run the `--check` command to compare synchronicity between cloud and local.

To view the summary that `--check` outputs without checking the server, `--summary` will count the files from each status.

```bash
➜ user @ ~/movies pqpvsf --check
0% ... 100% - 0 new files and 0 updates found
- Changed files:      2
- Partially Uploaded: 1
- Synchronized files: 3
```

Use `--sync` to begin uploading each file in queue. Sync also handles resuming the upload, and keeps track of the throttle in order to not surpass the rate limit.

```bash
➜ user @ ~/movies pqpvsf --sync
 ✅ Vid1.mp4: Completed
    🔳🔳🔳🔳🔳🔳🔳🔳🔳🔳 100%
    95.0 MB / 95.0 MB   ∙  in 0ʰ00‘45“

 📤 rec20250215.mov: Uploading
    🔳🔳🔳🔳🔳🔳🔳⬜⬜⬜ 73%
    6.3 MB / 8.0 MB     ∙  in 0ʰ00‘28“

 ⏸️ thirdvid.mkv: Changed, Upload Paused
    🔳🔳🔳🔳⬜⬜⬜⬜⬜⬜ 46%
    137.8 MB / 182.3 MB ∙  in 0ʰ03‘58“

 🔄 what.mov: Queued
    ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0%
    0.0 B / 4.5 GB      ∙  in 2ʰ15‘40“

➜ user @ ~/movies ^C
```

To synchronize only some selected files:

```bash
pqpvsf file001.mp4 file002.mp4 file003.mp4 --sync
```

### Editing Metadata

Manage all of a file's metadata with an external editor,
or update a single metadata value directly from the terminal:

```bash
# Open text editor:
➜ user @ ~/movies pqpvsf rec20250215.mov --manage

# Add or Edit: set key KEY value VALUE
➜ user @ ~/movies pqpvsf rec20250215.mov --set --key Title --value "Recording of my cat yawning"

# Abbreviated form: set KEY VALUE
➜ user @ ~/movies pqpvsf rec20250215.mov --set "camera" "Arriflex 16ST"

# To remove the record of an metadata: set delete KEY
➜ user @ ~/movies pqpvsf rec20250215.mov --set --delete Desc
```

> &nbsp; <br />
> ⚠️ **Important**: <br />
>
> Remember to run `--check` after <br />
> any changes made to metadata, <br />
> and `--sync` to push the changes!
> 
> ---
>
> `--check` tells to the sync queue that<br />
> there are files that need to be synced;<br />
>
> ---
>
> `--sync` synchronizes the files. <br />
> &nbsp;

## Contributing

Please do.

## Credits

Made by `@N²BL` with love and dedication.

`(A × N)² × B × L`  = `ANNIBAL`.

A Huge Special Thanks to the `Long` support that `Mike` gave throughout the whole development of PanQPlex! [[]]'s


