from app.schemas.knowledge_evidence import (
    KnowledgeEvidence,
)
from app.workspace.manager import (
    TaskWorkspace,
)


class KnowledgeEvidenceStore:

    def __init__(
        self,
        task_id: str,
        todo_id: str,
    ):

        self.todo_id = todo_id

        self.workspace = (
            TaskWorkspace(
                task_id=task_id
            )
        )

        self.path = (
            f"knowledge/"
            f"{todo_id}.json"
        )


    def save(
        self,
        evidences: list[
            KnowledgeEvidence
        ],
    ) -> list[
        KnowledgeEvidence
    ]:

        if self.workspace.exists(
            self.path
        ):

            data = (
                self.workspace.read_json(
                    self.path
                )
            )

        else:

            data = {
                "todo_id":
                    self.todo_id,

                "evidences":
                    [],
            }


        existing = {
            item["evidence_id"]: item
            for item
            in data["evidences"]
        }


        current = []


        for evidence in evidences:

            if (
                evidence.evidence_id
                not in existing
            ):

                item = (
                    evidence.model_dump()
                )

                data[
                    "evidences"
                ].append(
                    item
                )

                existing[
                    evidence.evidence_id
                ] = item


            current.append(
                evidence
            )


        self.workspace.write_json(
            self.path,
            data,
        )


        return current