# CURRENT_STATE
updated_at: 2026-10-24
git_head: 6b9c6f7
branch: overhaul/neo-brutal
architect_sha256: db26d7463fae63c6defc3bfc3b4f503865d32a31eb1e97066e274a6875771f4e
harness: codex; orchestrator gpt-6.1-sol/medium; customworkers gpt-5.6-luna/high (owner override); cap2
archetype: Neo-Brutal Motorsport(light), ADR007approved
last_eval_score: baseline51.2974358974359, obsolete forcurrentcode, NOTpresentable; fullscoreatT430

## Verified phase facts
- Phases0–2 complete. Phase3 T330accepted3afff87; T331inprogress, main1810lines (target<=120). Phase5 T3602ad337f/T3611e61efd/T362c0781f9/T36313f614a complete; T364runtime/T365/T366pending. Otherphasesunfinished; ownerrequestsall12, unattended.
- Phase2 preservescookie/CSRF/securityheaders/CORS/logoutrevocation+HTTP/WSrejecttests, additive migration004 onlydisposable, ADR011live/ready. Sourcehistory/ADRs remainauthoritative; no authchangesinrecentmoves.
- T330 permanentAPI snapshot9 + union7 + realGETgoldens14; runtime_route_registration2 addedafterduplicateroutefinding3343d87/fix7eeb81d. Requiredinput9REDregressionsfixed2c78430 (27focusedPASS); coversrequiredfields only, notallconstraints. NeverassumegreenOpenAPIprovesrouteuniqueness.
- Currentbackend rootfull227PASS0skip/livePASSafterT44214exportrepair ANDafterT44212tickwiring (logsT44214.full/T44212.full.raw.log). RootRuffall0, mypy211errors19/46files; strictzeroT339pending, no gate loosened.
- T331 exactmoves: SQLdbms+Mongo modules, stewardsread/create/decision89c82af; decisionimportremovalcaused7FAIL220PASS inrootfull. Repair5ee4710 restoredexplicitDecision/IncidentIn exports;18focusedPASS/full227PASS. PreservelegacyPythonaliases infuturemoves. T44212 46129c0 nowusesexactcoretick8275aab, old127linebodyremoved;22snapshot/runtime/replay/modelcasesPASS. Stagedcopy/wiretwoatomicsteps keeps150linebudget; no lastingduplicate.
- Frontend Tailwind4.3.3+adapter/tokens/fonts SpaceGrotesk500/700+Mono400/700/44pxfirstskiplink. Rootbuild/lint/types0afterT44215;85axe+4keyboardPASSafterlegacycontrastfix159692d; previousT361925nonpalettechecksPASS. Newunusedprimitivebrowserintegrationstillpendingstyleguide; actualdarkUIlightpaletteFAILisexpecteduntilPh7, never skipped/widened.
- SharedCSS/textures all4globalCSSgates0; staticplinthshadow, reducedguard, paletteactual1440rolesnearestscorer/gates unchanged. UIlibraryaccepted: button/card6eefdaa, badges e4a3f6c, inputs/field72a5b82, motifs/marquee/stat8ba857e, skeleton/fivestate0bd674b, modal/tabs38ae29f, table0e166fc. Typed cn/reduced/FLIP/flash47c0408 anddelayload/native-dialog/demo471cb56; runtimeT366pending.

## Active work / next
- Active two W3 workers: T44225 primitive/browser gates and T44226 actual mounted motion-hook tests, disjoint clones. Guide24fae87 (production404 guard), state fixtures324c60b and lap wiringef0dee3 accepted. Root guide build/lint/types0, lap wiring full227PASS0skip/livePASS. Candidate primitive browser0/30 because app/__nb was private and returned404; T44228 escapes firstunderscore to preserve /__nb. Prior production404 alone was insufficient. No accept during Next checks. After specs actual browser all5projects then close T364/T365/T366 only on green. Remaining plan docs/overhaul-plan.md.
- LatestT44212 rootfull227PASS0skip/livePASS, rootbuildafterT44215exit0, noAPI/schemafeaturechanges. W1scopechecks re-reviewedcomponentcontrast/naming/legacyCSSconflicts/roweventguards beforeaccept. Workerincorrectstaticcounts/extraenvelopekeys normalized, actualnumstatschecked, exactVerifyrootrerun.

## Contracts and safety
- Only overhaul/neo-brutal; commitsONLYaccept.sh, everyVerifyrootrerun, <=3files/150authoredchangedlines/task. Workersfreshpacket-only customrolesnooverrides afterprofile2bc94fb; explicittoolbindings5.6/high andsuccessfulresultsconfirmavailability. Noquotablocker now. Atmost2running, no workercommits.
- Never.env/secrets, recursive removal, realDB/schema/volume writes. DBonlyapexgrid-test(PG15432/Mongo27018), projectlabelschecked; realbackendnosourcebind/reload. Ownerstatus.sh paths excluded/unmodified; preserveownerrun-loopedits. APIwirechangesneedownADR; currentpuremovespreservecontracts.
- .agent/orchestrate.py clone/integrate/mark helpers persist; integrateonepatchthenacceptbeforeanother. NEVERacceptduringNextbuild/devcheck becausegeneratednext-envtemporarilychanges. .agent/check-frontend-build.py andcheck-frontend-browser.py restoreoriginalnext-envandkillonlyownrandomportserver.

## Open risks
- T331remaininggiantmodules; typedfactory/helpers temporaryT332 debt, strictmypy211 tozeroT339. Architecturelockunchangedverified. Sourceclasses/hooks/copy/aria/hashroutes/allfeaturesmustremain;fivestates/44targets/tokens/reducedmotion mandatory.
- P3bundlecheckerT44132 misseslayout/sharedinitialassets; LighthouseCLIabsentP1/P2NOT_RUN, FPS17msuntilT41316.7. HostedCI NOT_RUN. No fullscore/deliveryclaimbefore>=95/allhardgates/noNOT_RUN.
- W1 T44222 review caught nested main and dead modal Close button; corrected before acceptance. W2T44213 accidentallycreatedrootuse-nb-demo.ts; removedonlyownunacceptedcopybeforeaccept, nowonlyclone/rootacceptedfiles correct. Additionalnativeclose staleeventguard included. Neverstagerootaccidentalworkerfileswithothertask.

## Orchestrator direct edits
- Zeroauthoredproductlines. Onlyarchitecture/config/ADRs/packets/state/envelopes/orchestration/rootplanneddependencyinstalls; integratingworkerpatchesisnotauthorship. Modeloverride changed3Codexprofiles/models.envonly, cap/effort/orchestratorunchanged. npm-generatedlockexceptionexplicitownerplannedinstall, no newdepsrecently.








- T-44227 accepted225b2b8: Staged exact lock transaction helpers in focused typed factory; next atomic task wires aliases and removes main bodies. Verify0.

- T-44228 accepted6b9c6f7: Escaped private folder prefix so planned /__nb guide is actually routable in development; preserved identical production404 guard. Verify0.
