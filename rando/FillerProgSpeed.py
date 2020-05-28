
import copy, random, sys

from rando.Filler import Filler
from rando.FillerRandom import FillerRandom, FillerRandomItems
from rando.Choice import ItemThenLocChoiceProgSpeed
from rando.RandoServices import ComebackCheckType
from rando.Items import ItemManager
from rando.ItemLocContainer import ItemLocContainer, LooseItemLocContainer, getLocListStr, getItemListStr
from parameters import infinity
from graph_access import GraphUtils, getAccessPoint

progSpeeds = ['slowest', 'slow', 'medium', 'fast', 'fastest']

# algo settings depending on prog speed, and unrelated to choice
class ProgSpeedParameters(object):
    def __init__(self, restrictions):
        self.restrictions = restrictions

    def getMinorHelpProb(self, progSpeed):
        if self.restrictions.split != 'Major':
            return 0
        if progSpeed == 'slowest':
            return 0.16
        elif progSpeed == 'slow':
            return 0.33
        elif progSpeed == 'medium':
            return 0.5
        return 1

    def getItemLimit(self, progSpeed):
        itemLimit = 105
        if progSpeed == 'slow':
            itemLimit = 21
        elif progSpeed == 'medium':
            itemLimit = 12
        elif progSpeed == 'fast':
            itemLimit = 5
        elif progSpeed == 'fastest':
            itemLimit = 1
        if self.restrictions.split == 'Chozo':
            itemLimit = int(itemLimit / 4)
        minLimit = itemLimit - int(itemLimit/5)
        maxLimit = itemLimit + int(itemLimit/5)
        if minLimit == maxLimit:
            itemLimit = minLimit
        else:
            itemLimit = random.randint(minLimit, maxLimit)
        return itemLimit

    def getLocLimit(self, progSpeed):
        locLimit = -1
        if progSpeed == 'slow':
            locLimit = 1
        elif progSpeed == 'medium':
            locLimit = 2
        elif progSpeed == 'fast':
            locLimit = 3
        elif progSpeed == 'fastest':
            locLimit = 4
        return locLimit

    def getProgressionItemTypes(self, progSpeed):
        progTypes = ItemManager.getProgTypes()
        progTypes.append('Charge')
        if progSpeed == 'slowest':
            return progTypes
        else:
            progTypes.remove('HiJump')
            progTypes.remove('Charge')
        if progSpeed == 'slow':
            return progTypes
        else:
            progTypes.remove('Bomb')
            progTypes.remove('Grapple')
        if progSpeed == 'medium':
            return progTypes
        else:
            progTypes.remove('Ice')
            progTypes.remove('SpaceJump')
        if progSpeed == 'fast':
            return progTypes
        else:
            progTypes.remove('SpeedBooster')
        if progSpeed == 'fastest':
            return progTypes # only morph, varia, gravity
        raise RuntimeError("Unknown prog speed " + progSpeed)

    def getPossibleSoftlockProb(self, progSpeed):
        if progSpeed == 'slowest':
            return 1
        if progSpeed == 'slow':
            return 0.66
        if progSpeed == 'medium':
            return 0.33
        if progSpeed == 'fast':
            return 0.1
        if progSpeed == 'fastest':
            return 0
        raise RuntimeError("Unknown prog speed " + progSpeed)

    def getChozoSecondPhaseRestrictionProb(self, progSpeed):
        if progSpeed == 'slowest':
            return 0
        if progSpeed == 'slow':
            return 0.16
        if progSpeed == 'medium':
            return 0.5
        if progSpeed == 'fast':
            return 0.9
        return 1

# algo state used for rollbacks
class FillerState(object):
    def __init__(self, filler):
        self.container = copy.copy(filler.container)
        self.ap = filler.ap
        self.states = filler.states[:]
        self.progressionItemLocs = filler.progressionItemLocs[:]
        self.progressionStatesIndices = filler.progressionStatesIndices[:]

    def apply(self, filler):
        filler.container = self.container
        filler.ap = self.ap
        filler.states = self.states
        filler.progressionItemLocs = self.progressionItemLocs
        filler.progressionStatesIndices = self.progressionStatesIndices
        filler.cache.reset()

    def __eq__(self, rhs):
        if rhs is None:
            return False
        eq = self.container == rhs.container
        eq &= self.ap == rhs.ap
        eq &= self.progressionStatesIndices == rhs.progressionStatesIndices
        return eq

class FillerProgSpeed(Filler):
    def __init__(self, graphSettings, areaGraph, restrictions, container):
        super(FillerProgSpeed, self).__init__(graphSettings.startAP, areaGraph, restrictions, container)
        distanceProp = 'GraphArea' if graphSettings.areaRando else 'Area'
        self.stdStart = GraphUtils.isStandardStart(self.startAP)
        self.choice = ItemThenLocChoiceProgSpeed(restrictions, distanceProp, self.services)
        self.progSpeedParams = ProgSpeedParameters(restrictions)

    def initFiller(self):
        super(FillerProgSpeed, self).initFiller()
        self.states = []
        self.progressionItemLocs = []
        self.progressionStatesIndices = []
        self.rollbackItemsTried = {}
        self.lastFallbackState = None
        self.initState = FillerState(self)

    def determineParameters(self):
        speed = self.settings.progSpeed
        if speed == 'variable':
            speed = random.choice(progSpeeds)
        self.choice.determineParameters(speed)
        self.minorHelpProb = self.progSpeedParams.getMinorHelpProb(speed)
        self.itemLimit = self.progSpeedParams.getItemLimit(speed)
        self.locLimit = self.progSpeedParams.getLocLimit(speed)
        self.possibleSoftlockProb = self.progSpeedParams.getPossibleSoftlockProb(speed)
        self.progressionItemTypes = self.progSpeedParams.getProgressionItemTypes(speed)
        if self.restrictions.isEarlyMorph() and 'Morph' in self.progressionItemTypes:
            self.progressionItemTypes.remove('Morph')
        collectedAmmo = self.container.getCollectedItems(lambda item: item['Category'] == 'Ammo')
        collectedAmmoTypes = set([item['Type'] for item in collectedAmmo])
        ammos = ['Missile', 'Super', 'PowerBomb']
        if 'Super' in collectedAmmoTypes:
            ammos.remove('Missile')
        self.progressionItemTypes += [ammoType for ammoType in ammos if ammoType not in collectedAmmoTypes]

    def chooseItemLoc(self, itemLocDict, possibleProg):
        return self.choice.chooseItemLoc(itemLocDict, possibleProg, self.progressionItemLocs, self.ap, self.container)

    def currentLocations(self, item=None):
        return self.services.currentLocations(self.ap, self.container, item=item)

    def getComebackCheck(self):
        if self.isEarlyGame():
            return ComebackCheckType.NoCheck
        if random.random() >= self.possibleSoftlockProb:
            return ComebackCheckType.ComebackWithoutItem
        return ComebackCheckType.JustComeback

    # from current accessible locations and an item pool, generate an item/loc dict.
    # return item/loc, or None if stuck
    def generateItem(self):
        itemLocDict, possibleProg = self.services.getPossiblePlacements(self.ap, self.container, self.getComebackCheck())
        if self.isEarlyGame():
            # cheat a little bit if non-standard start: place early
            # progression away from crateria/blue brin if possible
            startAp = getAccessPoint(self.startAP)
            if startAp.GraphArea != "Crateria":
                newItemLocDict = {}
                for w, locs in itemLocDict.items():
                    filtered = [loc for loc in locs if loc['GraphArea'] != 'Crateria']
                    if len(filtered) > 0:
                        newItemLocDict[w] = filtered
                if len(newItemLocDict) > 0:
                    itemLocDict = newItemLocDict
        itemLoc = self.chooseItemLoc(itemLocDict, possibleProg)
        self.log.debug("generateItem. itemLoc="+("None" if itemLoc is None else itemLoc['Item']['Type']+"@"+itemLoc['Location']['Name']))
        return itemLoc

    def getCurrentState(self):
        return self.states[-1] if len(self.states) > 0 else self.initState

    def appendCurrentState(self):
        curState = FillerState(self)
        self.states.append(curState)
        curState.states.append(curState)

    def collect(self, itemLoc):
        isProg = self.services.isProgression(itemLoc['Item'], self.ap, self.container)
        super(FillerProgSpeed, self).collect(itemLoc)
        if isProg:
            n = len(self.states)
            self.log.debug("prog indice="+str(n))
            self.progressionStatesIndices.append(n)
            self.progressionItemLocs.append(itemLoc)
        self.appendCurrentState()
        self.cache.reset()

    def isProgItem(self, item):
        if item['Type'] in self.progressionItemTypes:
            return True
        return self.services.isProgression(item, self.ap, self.container)

    def isEarlyGame(self):
        return len(self.progressionStatesIndices) <= 2 if self.stdStart else len(self.progressionStatesIndices) <= 3

    # check if remaining locations pool is conform to rando settings when filling up
    # with non-progression items
    def checkLocPool(self):
        sm = self.container.sm
 #       self.log.debug("checkLocPool {}".format([it['Name'] for it in self.itemPool]))
        if self.locLimit <= 0:
            return True
        progItems = self.container.getItems(self.isProgItem)
        self.log.debug("checkLocPool. progItems {}".format([it['Name'] for it in progItems]))
 #       self.log.debug("curItems {}".format([it['Name'] for it in self.currentItems]))
        if len(progItems) == 0:
            return True
        isMinorProg = any(self.restrictions.isItemMinor(item) for item in progItems)
        isMajorProg = any(self.restrictions.isItemMajor(item) for item in progItems)
        accessibleLocations = []
#        self.log.debug("unusedLocs: {}".format([loc['Name'] for loc in self.unusedLocations]))
        locs = self.currentLocations()
        for loc in locs:
            majAvail = self.restrictions.isLocMajor(loc)
            minAvail = self.restrictions.isLocMinor(loc)
            if ((isMajorProg and majAvail) or (isMinorProg and minAvail)) \
               and self.services.locPostAvailable(sm, loc, None):
                accessibleLocations.append(loc)
        self.log.debug("accesLoc {}".format([loc['Name'] for loc in accessibleLocations]))
        if len(accessibleLocations) <= self.locLimit:
            sys.stdout.write('|')
            sys.stdout.flush()
            return False
        # check that there is room left in all main areas
        room = {'Brinstar' : 0, 'Norfair' : 0, 'WreckedShip' : 0, 'LowerNorfair' : 0, 'Maridia' : 0 }
        if not self.stdStart:
            room['Crateria'] = 0
        for loc in self.container.unusedLocations:
            majAvail = self.restrictions.isLocMajor(loc)
            minAvail = self.restrictions.isLocMinor(loc)
            if loc['Area'] in room and ((isMajorProg and majAvail) or (isMinorProg and minAvail)):
                room[loc['Area']] += 1
        for r in room.values():
            if r > 0 and r <= self.locLimit:
                sys.stdout.write('|')
                sys.stdout.flush()
                return False
        return True

    def addEnergyAsNonProg(self):
        return self.restrictions.split == 'Chozo'

    def nonProgItemCheck(self, item):
        return (item['Category'] == 'Energy' and self.addEnergyAsNonProg()) or (not self.stdStart and item['Category'] == 'Ammo') or (self.restrictions.isEarlyMorph() and item['Type'] == 'Morph') or not self.isProgItem(item)

    def getNonProgItemPoolRestriction(self):
        return self.nonProgItemCheck

    def pickHelpfulMinor(self, item):
        self.helpfulMinorPicked = not self.container.hasItemTypeInPool(item['Type'])
        return self.helpfulMinorPicked

    def getNonProgItemPoolRestrictionStart(self):
        self.helpfulMinorPicked = random.random() >= self.minorHelpProb
        return lambda item: (item['Category'] == 'Ammo' and not self.helpfulMinorPicked and self.pickHelpfulMinor(item)) or self.nonProgItemCheck(item)

    # return True if stuck, False if not
    def fillNonProgressionItems(self):
        if self.itemLimit <= 0:
            return False
        poolRestriction = self.getNonProgItemPoolRestrictionStart()
        self.container.restrictItemPool(poolRestriction)
        if self.container.isPoolEmpty():
            self.container.unrestrictItemPool()
            return False
        itemLocation = None
        nItems = 0
        locPoolOk = True
        self.log.debug("NON-PROG")
        while not self.container.isPoolEmpty() and nItems < self.itemLimit and locPoolOk:
            itemLocation = self.generateItem()
            if itemLocation is not None:
                nItems += 1
                self.log.debug("fillNonProgressionItems: {} at {}".format(itemLocation['Item']['Name'], itemLocation['Location']['Name']))
                # doing this first is actually important, as state is saved in collect
                self.container.unrestrictItemPool()
                self.collect(itemLocation)
                locPoolOk = self.checkLocPool()
                poolRestriction = self.getNonProgItemPoolRestriction()
                self.container.restrictItemPool(poolRestriction)
            else:
                break
        self.container.unrestrictItemPool()
        return itemLocation is None

    def getItemFromStandardPool(self):
        itemLoc = self.generateItem()
        isStuck = itemLoc is None
        if not isStuck:
            sys.stdout.write('-')
            sys.stdout.flush()
            self.collect(itemLoc)
        return isStuck

    def initRollbackPoints(self):
        minRollbackPoint = 0
        maxRollbackPoint = len(self.states) - 1
        if len(self.progressionStatesIndices) > 0:
            minRollbackPoint = self.progressionStatesIndices[-1]
        self.log.debug('initRollbackPoints: min=' + str(minRollbackPoint) + ", max=" + str(maxRollbackPoint))
        return minRollbackPoint, maxRollbackPoint

    def initRollback(self, isFakeRollback):
        self.log.debug('initRollback: progressionStatesIndices 1=' + str(self.progressionStatesIndices))
        if len(self.progressionStatesIndices) > 0 and self.progressionStatesIndices[-1] == len(self.states) - 1:
            if isFakeRollback == True: # in fake rollback case we refuse to remove any progression
                return
            # the state we are about to remove was a progression state
            self.progressionStatesIndices.pop()
        if len(self.states) > 0:
            self.states.pop() # remove current state, it's the one we're stuck in
        self.log.debug('initRollback: progressionStatesIndices 2=' + str(self.progressionStatesIndices))

    def getSituationId(self):
        progItems = str(sorted([il['Item']['Type'] for il in self.progressionItemLocs]))
        position = str(sorted([ap.Name for ap in self.services.currentAccessPoints(self.ap, self.container)]))
        return progItems+'/'+position

    def hasTried(self, itemLoc):
        if self.isEarlyGame():
            return False
        itemType = itemLoc['Item']['Type']
        situation = self.getSituationId()
        ret = False
        if situation in self.rollbackItemsTried:
            ret = itemType in self.rollbackItemsTried[situation]
            if ret:
                self.log.debug('has tried ' + itemType + ' in situation ' + situation)
        return ret

    def updateRollbackItemsTried(self, itemLoc):
        itemType = itemLoc['Item']['Type']
        situation = self.getSituationId()
        if situation not in self.rollbackItemsTried:
            self.rollbackItemsTried[situation] = []
        self.log.debug('adding ' + itemType + ' to situation ' + situation)
        self.rollbackItemsTried[situation].append(itemType)

    # goes back in the previous states to find one where
    # we can put a progression item
    def rollback(self):
        nItemsAtStart = len(self.container.currentItems)
        nStatesAtStart = len(self.states)
        self.log.debug("rollback BEGIN: nItems={}, nStates={}".format(nItemsAtStart, nStatesAtStart))
        currentState = self.getCurrentState()
        ret = None
        # we can be in a 'fake rollback' situation where we rollback
        # just after non prog phase without checking normal items first (we
        # do this for more randomness, to avoid placing items in postavail locs
        # like spospo etc. too often).
        # in this case, we won't remove any prog items since we're not actually
        # stuck
        if not self.isEarlyGame():
            ret = self.generateItem()
        isFakeRollback = ret is not None
        self.log.debug('isFakeRollback=' + str(isFakeRollback))
        self.initRollback(isFakeRollback)
        if len(self.states) == 0:
            self.initState.apply(self)
            self.log.debug("rollback END initState apply, nCurLocs="+str(len(self.currentLocations())))
            if self.vcr != None:
                self.vcr.addRollback(nStatesAtStart)
            sys.stdout.write('<'*nStatesAtStart)
            sys.stdout.flush()
            return None
        # to stay consistent in case no solution is found as states list was popped in init
        fallbackState = self.getCurrentState()
        if fallbackState == self.lastFallbackState:
            # we're stuck there, rewind more in fallback
            fallbackState = self.states[-2] if len(self.states) > 1 else self.initState
        self.lastFallbackState = fallbackState
        i = 0
        possibleStates = []
        self.log.debug('rollback. nStates='+str(len(self.states)))
        while i >= 0 and len(possibleStates) == 0:
            states = self.states[:]
            minRollbackPoint, maxRollbackPoint = self.initRollbackPoints()
            i = maxRollbackPoint
            while i >= minRollbackPoint and len(possibleStates) < 3:
                state = states[i]
                state.apply(self)
                itemLoc = self.generateItem()
                if itemLoc is not None and not self.hasTried(itemLoc) and self.services.isProgression(itemLoc['Item'], self.ap, self.container):
                    possibleStates.append((state, itemLoc))
                i -= 1
            # nothing, let's rollback further a progression item
            if len(possibleStates) == 0 and i >= 0:
                if len(self.progressionStatesIndices) > 0 and isFakeRollback == False:
                    sys.stdout.write('!')
                    sys.stdout.flush()
                    self.progressionStatesIndices.pop()
                else:
                    break
        if len(possibleStates) > 0:
            (state, itemLoc) = random.choice(possibleStates)
            self.updateRollbackItemsTried(itemLoc)
            state.apply(self)
            ret = itemLoc
            if self.vcr != None:
                nRoll = nItemsAtStart - len(self.container.currentItems)
                if nRoll > 0:
                    self.vcr.addRollback(nRoll)
        else:
            if isFakeRollback == False:
                self.log.debug('fallbackState apply')
                fallbackState.apply(self)
                if self.vcr != None:
                    self.vcr.addRollback(1)
            else:
                self.log.debug('currentState restore')
                currentState.apply(self)
        sys.stdout.write('<'*(nStatesAtStart - len(self.states)))
        sys.stdout.flush()
        self.log.debug("rollback END: {}".format(len(self.container.currentItems)))
        return ret

    def step(self, onlyBossCheck=False):
        self.cache.reset()
        if self.services.canEndGame(self.container) and self.settings.progSpeed not in ['slowest', 'slow']:
            (itemLocDict, isProg) = self.services.getPossiblePlacementsNoLogic(self.container)
            itemLoc = self.chooseItemLoc(itemLocDict, False)
            assert itemLoc is not None
            self.ap = self.services.collect(self.ap, self.container, itemLoc)
            return True
        self.determineParameters()
        # fill up with non-progression stuff
        isStuck = self.fillNonProgressionItems()
        if not self.container.isPoolEmpty():
            if not isStuck:
                isStuck = self.getItemFromStandardPool()
            if isStuck:
                if onlyBossCheck == False and self.services.onlyBossesLeft(self.ap, self.container):
                    self.settings.maxDiff = infinity
                    return self.step(onlyBossCheck=True)
                if onlyBossCheck == True:
                    # we're stuck even after bumping diff.
                    # it was a onlyBossesLeft false positive, restore max diff
                    self.settings.maxDiff = self.maxDiff
                # check that we're actually stuck
                nCurLocs = len(self.currentLocations())
                nLocsLeft = len(self.container.unusedLocations)
                itemLoc = None
                if nCurLocs < nLocsLeft:
                    # stuck, rollback to make progress if we can't access everything yet
                    itemLoc = self.rollback()
                if itemLoc is not None:
                    self.collect(itemLoc)
                    isStuck = False
                else:
                    isStuck = self.getItemFromStandardPool()
        return not isStuck

    def getProgressionItemLocations(self):
        return self.progressionItemLocs


class FillerRandomNoCopy(FillerRandom):
    def __init__(self, startAP, graph, restrictions, container, diffSteps=0):
        super(FillerRandomNoCopy, self).__init__(startAP, graph, restrictions, container, diffSteps)

    def initContainer(self):
        self.container = self.baseContainer

class FillerProgSpeedChozoSecondPhase(Filler):
    def __init__(self, startAP, graph, restrictions, container):
        super(FillerProgSpeedChozoSecondPhase, self).__init__(startAP, graph, restrictions, container)
        # turn baseContainer into a loose container with nothing collected
        self.baseContainer = LooseItemLocContainer(self.baseContainer.sm,
                                                   self.baseContainer.itemPool,
                                                   self.baseContainer.unusedLocations)
        self.firstPhaseItemLocs = container.itemLocations
        self.progSpeedParams = ProgSpeedParameters(self.restrictions)

    def initContainer(self):
        self.container = self.baseContainer

    def initFiller(self):
        super(FillerProgSpeedChozoSecondPhase, self).initFiller()
        self.conditions = [
            ('Missile', lambda sm: sm.canOpenRedDoors()),
            ('Super', lambda sm: sm.canOpenGreenDoors()),
            ('PowerBomb', lambda sm: sm.canOpenYellowDoors())
        ]
        self.container.resetCollected()
        self.firstPhaseContainer = ItemLocContainer(self.container.sm,
                                                    [il['Item'] for il in self.firstPhaseItemLocs],
                                                    [il['Location'] for il in self.firstPhaseItemLocs])
        self.firstPhaseIndex = 0

    def nextMetCondition(self):
        for cond in self.conditions:
            diff = cond[1](self.container.sm)
            if diff.bool == True and diff.difficulty <= self.settings.maxDiff:
                return cond
        return None

    def currentLocations(self):
        curLocs = self.services.currentLocations(self.ap, self.container)
        return self.services.getPlacementLocs(self.ap, self.container, ComebackCheckType.JustComeback, None, curLocs)

    def determineParameters(self):
        speed = self.settings.progSpeed
        if speed == 'variable':
            speed = random.choice(progSpeeds)
        self.restrictedItemProba = self.progSpeedParams.getChozoSecondPhaseRestrictionProb(speed)

    def step(self):
        if len(self.conditions) > 1:
            self.determineParameters()
            curLocs = []
            while self.firstPhaseIndex < len(self.firstPhaseItemLocs):
                self.cache.reset()
                newCurLocs = [loc for loc in self.currentLocations() if loc not in curLocs]
                curLocs += newCurLocs
                cond = self.nextMetCondition()
                if cond is not None:
                    self.log.debug('step. cond item='+cond[0])
                    self.conditions.remove(cond)
                    break
                self.ap = self.services.collect(self.ap, self.firstPhaseContainer, self.firstPhaseItemLocs[self.firstPhaseIndex])
                self.firstPhaseIndex += 1
            self.log.debug('step. curLocs='+getLocListStr(curLocs))
            restrictedItemTypes = [cond[0] for cond in self.conditions]
            self.log.debug('step. restrictedItemTypes='+str(restrictedItemTypes))
            itemPool = []
            while len(itemPool) < len(curLocs):
                item = random.choice(self.container.itemPool)
                if item['Type'] not in restrictedItemTypes or random.random() < self.restrictedItemProba:
                    itemPool.append(item)
            self.log.debug('step. itemPool='+getItemListStr(itemPool))
            cont = ItemLocContainer(self.container.sm, itemPool, curLocs)
            self.container.transferCollected(cont)
            filler = FillerRandomItems(self.ap, self.graph, self.restrictions, cont)
            (stuck, itemLocs, prog) = filler.generateItems()
            assert not stuck
            for itemLoc in itemLocs:
                if itemLoc['Location'] in self.container.unusedLocations:
                    self.log.debug("step. POST COLLECT "+itemLoc['Item']['Type']+" at "+itemLoc['Location']['Name'])
                    self.container.collect(itemLoc)
        else:
            # merge collected of 1st phase and 2nd phase so far for seed to be solvable by random fill
            self.container.itemLocations += self.firstPhaseItemLocs
            self.log.debug("step. LAST FILL. cont: "+self.container.dump())
            filler = FillerRandomNoCopy(self.startAP, self.graph, self.restrictions, self.container, diffSteps=100)
            (stuck, itemLocs, prog) = filler.generateItems()
            assert not stuck
        return True
