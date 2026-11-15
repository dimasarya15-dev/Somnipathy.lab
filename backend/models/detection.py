"""Tabel penyimpanan hasil deteksi dan rekomendasinya."""

from __future__ import annotations

from datetime import datetime

from backend.extensions import db

# BigAutoIncrement: MySQL memakai BIGINT, SQLite (untuk pengujian) memakai INTEGER
BigIntPK = db.BigInteger().with_variant(db.Integer, "sqlite")


class Detection(db.Model):
    """Satu kali proses deteksi beserta salinan data masukannya."""

    __tablename__ = "detections"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    session_token = db.Column(db.String(36), nullable=False, index=True)
    input_data = db.Column(db.JSON, nullable=False)
    prediction = db.Column(db.String(64), nullable=False, index=True)
    confidence = db.Column(db.Numeric(5, 4), nullable=False)
    probabilities = db.Column(db.JSON, nullable=True)
    model_version = db.Column(db.String(32), nullable=False)
    created_at = db.Column(
        db.DateTime, nullable=False, default=datetime.now, index=True
    )

    recommendations = db.relationship(
        "DetectionRecommendation",
        back_populates="detection",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="DetectionRecommendation.id",
    )

    def to_dict(self, include_input: bool = False) -> dict:
        """Bentuk JSON untuk API / template."""
        data = {
            "id": self.id,
            "prediction": self.prediction,
            "confidence": float(self.confidence) if self.confidence is not None else None,
            "probabilities": self.probabilities or {},
            "model_version": self.model_version,
            "created_at": self.created_at.isoformat(timespec="seconds")
            if self.created_at
            else None,
            "recommendations": [rec.to_dict() for rec in self.recommendations],
        }
        if include_input:
            data["input"] = self.input_data
        return data

    def __repr__(self) -> str:  # pragma: no cover - bantuan debugging
        return f"<Detection {self.id} {self.prediction} {self.confidence}>"


class DetectionRecommendation(db.Model):
    """Rekomendasi hasil aturan untuk satu deteksi."""

    __tablename__ = "detection_recommendations"

    id = db.Column(BigIntPK, primary_key=True, autoincrement=True)
    detection_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        db.ForeignKey("detections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_id = db.Column(db.String(32), nullable=False)
    category = db.Column(db.String(64), nullable=False)
    severity = db.Column(db.String(16), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)

    detection = db.relationship("Detection", back_populates="recommendations")

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "category": self.category,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DetectionRecommendation {self.rule_id}>"
