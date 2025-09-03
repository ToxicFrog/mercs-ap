TAGS=mercenaries-*
VERSION=0.1.0

all: apworld

apworld: version release/mercenaries-${VERSION}.apworld

version:
	tools/version-stamp "${TAGS}" mercenaries/VERSION

release/mercenaries-${VERSION}.apworld: mercenaries/* mercenaries/*/*
	zip -r release/mercenaries.apworld mercenaries
	cp release/mercenaries.apworld release/mercenaries-${VERSION}.apworld
	cp release/mercenaries.apworld ~/.local/share/Archipelago/worlds/

.PHONY: apworld
