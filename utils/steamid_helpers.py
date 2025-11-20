"""
Helper functions för SteamID validation och checking
Skapa denna fil: utils/steamid_helpers.py
"""

from database.database import async_session
from database.models import PlayerSteamID
from sqlalchemy import select
import logging

logger = logging.getLogger('TournamentBot.SteamIDHelpers')


async def has_linked_steamid(user_id: int) -> bool:
    """
    Kolla om en användare har länkat sitt SteamID
    
    Args:
        user_id: Discord user ID
    
    Returns:
        bool: True om användaren har länkat SteamID
    """
    async with async_session() as session:
        try:
            result = await session.execute(
                select(PlayerSteamID).where(
                    PlayerSteamID.user_id == user_id,
                    PlayerSteamID.verified == True
                )
            )
            steamid = result.scalar_one_or_none()
            return steamid is not None
        except Exception as e:
            logger.error(f'Fel vid check av SteamID för user {user_id}: {e}')
            return False


async def get_steamid(user_id: int) -> str | None:
    """
    Hämta en användares SteamID
    
    Args:
        user_id: Discord user ID
    
    Returns:
        str | None: SteamID eller None om inte länkat
    """
    async with async_session() as session:
        try:
            result = await session.execute(
                select(PlayerSteamID).where(
                    PlayerSteamID.user_id == user_id,
                    PlayerSteamID.verified == True
                )
            )
            steamid = result.scalar_one_or_none()
            return steamid.steam_id if steamid else None
        except Exception as e:
            logger.error(f'Fel vid hämtning av SteamID för user {user_id}: {e}')
            return None


async def check_team_steamids(team_id: int) -> tuple[bool, list[int]]:
    """
    Kolla om alla i ett lag har länkat SteamID
    
    Args:
        team_id: Team ID
    
    Returns:
        tuple[bool, list[int]]: (alla_har_steamid, lista_av_user_ids_utan_steamid)
    """
    from database.models import TeamMember
    
    async with async_session() as session:
        try:
            # Hämta alla team members
            result = await session.execute(
                select(TeamMember).where(TeamMember.team_id == team_id)
            )
            members = result.scalars().all()
            
            missing_steamids = []
            
            # Kolla varje medlem
            for member in members:
                has_steamid = await has_linked_steamid(member.user_id)
                if not has_steamid:
                    missing_steamids.append(member.user_id)
            
            return len(missing_steamids) == 0, missing_steamids
        
        except Exception as e:
            logger.error(f'Fel vid check av team SteamIDs för team {team_id}: {e}')
            return False, []