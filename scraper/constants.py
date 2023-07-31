"""Contains GQL query strings.
"""
TIERS = [
    "INTERNATIONAL",
    "DPC_QUALIFIER",
    "DPC_LEAGUE_QUALIFIER",
    "DPC_LEAGUE",
    "DPC_LEAGUE_FINALS",
    "MAJOR",
    "PROFESSIONAL",
]

INIT_DATA_QUERY = """
    query SeriesByLeagueQuery($leaguesRequest: LeagueRequestType!,
                              $takeSeries: Int!, 
                              $skipSeries: Int!) {
        leagues(request: $leaguesRequest) {
            id
            displayName
            startDateTime
            endDateTime
            tier
            region
            country
            series(take: $takeSeries, skip: $skipSeries) {
                id
                type
                matches {
                    id
                    startDateTime
                    endDateTime
                    durationSeconds
                    radiantTeam {
                        id
                        name
                    }
                    direTeam {
                        id
                        name
                    }
                    firstBloodTime
                    radiantKills
                    direKills
                    didRadiantWin
                    players {
                        isRadiant
                        steamAccount {
                            id
                            name
                            proSteamAccount {
                                name
                            }
                        }
                        hero {
                            id
                            displayName
                        }
                        kills
                        deaths
                        assists
                        networth
                        lane
                        position
                        role
                    }
                    gameVersionId
                }
            }
        }
    }
"""

CUSTOM_DATA_QUERY = """
    query MatchesByLeagueQuery($leaguesRequest: LeagueRequestType!,
                               $matchesRequest:  LeagueMatchesRequestType!) {
        leagues(request: $leaguesRequest) {
            id
            displayName
            startDateTime
            endDateTime
            tier
            region
            country
            matches(request: $matchesRequest) {
                series {
                    id
                    type
                }
                id
                startDateTime
                endDateTime
                durationSeconds
                radiantTeam {
                    id
                    name
                }
                direTeam {
                    id
                    name
                }
                firstBloodTime
                radiantKills
                direKills
                didRadiantWin
                players {
                    isRadiant
                    steamAccount {
                        id
                        name
                        proSteamAccount {
                            name
                        }
                    }
                    hero {
                        id
                        displayName
                    }
                    kills
                    deaths
                    assists
                    networth
                    lane
                    position
                    role
                }
                gameVersionId
            }
        }
    }
"""
