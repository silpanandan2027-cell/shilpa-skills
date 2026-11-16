#!/bin/bash
# Copy the official GTA VI images used by the edit into build/assets/rs/ under short names,
# and turn three of the site's sticker animations into transparent PNG frame sequences.
# Source: media downloaded from rockstargames.com/VI into $SRC (see README).
# These files are Rockstar's: they're kept out of git (.gitignore) and credited in the description.
set -e
SRC=${SRC:-/tmp/claude-0/rs/dl}
OUT=$(dirname "$0")/assets/rs
mkdir -p "$OUT/stickers"
pick() { cp "$SRC/img/$(ls "$SRC/img" | grep -F "$1" | head -1)" "$OUT/$2.jpg"; }

pick 'k4ak9okk485712'                       city_day        # aerial Vice City, daytime
pick 'desktop.00.5pzu2sm'                   city_night      # skyline at dusk
pick 'desktop.0iky3x6'                      beach_car       # Jason & Lucia, green car, beach
pick 'onlyInLeonidaDesktop'                 pool_float      # pool party, Leonida
pick 'ULTIMATE_EDITION_SQUALO_01'           boat_city       # speedboat, skyline
pick 'ULTIMATE_EDITION_SQUALO_03'           boat_ocean
pick 'ULTIMATE_EDITION_SQUALO_04'           boats_top
pick 'ULTIMATE_EDITION_SAFEHOUSE_VEHICLES_03' kayak_sunset
pick 'ULTIMATE_EDITION_SAFEHOUSE_VEHICLES_01' stilt_house
pick 'ULTIMATE_EDITION_VAPID_BUGGY_01'      buggy_mud
pick 'ULTIMATE_EDITION_VAPID_BUGGY_04'      truck_dirt
pick 'ULTIMATE_EDITION_GROTTI_CHEETAH_02'   cheetah_night
pick 'ULTIMATE_EDITION_GROTTI_CHEETAH_01'   cheetah_garage
pick 'ULTIMATE_EDITION_PTT_STORE_01'        store_crowd
pick 'ULTIMATE_EDITION_WYMAN_CAR_COLLECTION_01' beach_crowd
pick 'ULTIMATE_EDITION_STOCK_305_01'        graffiti_truck
pick 'ULTIMATE_EDITION_ELECTRIC_FANG_01'    tattoo_neon
pick 'ULTIMATE_EDITION_01'                  duo_sunset      # Lucia + Jason, sunset palms
pick 'ULTIMATE_EDITION_02'                  duo_car
pick 'ULTIMATE_EDITION_VICE_CITY_STYLE_03'  lucia
pick 'ULTIMATE_EDITION_VICE_CITY_STYLE_04'  jason
pick 'ULTIMATE_EDITION_VICE_CITY_STYLE_01'  duo_lounge
pick 'VINTAGE_VICE_CITY_PACK_01'            hotel_neon
pick 'VINTAGE_VICE_CITY_PACK_02'            port_sunset
pick 'VINTAGE_VICE_CITY_PACK_EXCLUSIVE_LOOKS_01' club
pick 'screenshotsDesktop'                   couple_neon
pick 'mediaDesktop'                         masks
pick 'musicDesktop'                         music_car
pick 'an-extended-look.0ijbsha5fo1te'       art_gas
pick 'launch-trailer.0_q-sdrgufc'           art_launch
pick 'pre-load.0h87nx'                      art_preload
pick '89834o94713o21'                       art_cover       # cover art with "November 19 2026"
pick 'ultimate_desktop_en_us'               art_ultimate
pick 'ULTIMATE_EDITION_HAWK_AND_LITTLE_MORGAN_REVOLVERS_01' revolver

# stickers: the top half of each video is colour, the bottom half is its alpha mask
sticker() {
  local f; f="$SRC/clips/$(ls "$SRC/clips" | grep -F "$1" | head -1)"
  mkdir -p "$OUT/stickers/$2"; rm -f "$OUT/stickers/$2"/*.png
  ffmpeg -v error -y -i "$f" -filter_complex \
    "[0]crop=iw:ih/2:0:0[c];[0]crop=iw:ih/2:0:ih/2,format=gray[m];[c][m]alphamerge,fps=15,scale=640:-2" \
    "$OUT/stickers/$2/%03d.png"
  echo "$2: $(ls "$OUT/stickers/$2" | wc -l) frames"
}
sticker '0f-99y62dfbwx' gator
sticker '0_ji97d~ir4ki' flamingo
sticker '0nk5gih2-3jni' crab
sticker '08xz5161.ed04' sun
ls "$OUT" | wc -l
